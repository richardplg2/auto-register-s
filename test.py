import ctypes
import threading
import time
from contextlib import contextmanager
from ctypes import sizeof
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import structlog
from NetSDK.NetSDK import NetClient
from NetSDK.SDK_Callback import fServiceCallBack
from NetSDK.SDK_Enum import EM_LOGIN_SPAC_CAP_TYPE
from NetSDK.SDK_Struct import (
    NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY,
    NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY,
)

from app.types.dahua_netsdk_types import DeviceAutoRegisterEvent

logger = structlog.get_logger(__name__)


@dataclass
class DeviceSession:
    device_id: str
    login_id: int
    ip: str
    port: int
    username: str
    password: str
    created_at: float
    last_used: float
    is_active: bool = True


@dataclass
class ListenerSession:
    host: str
    port: int
    handle: int
    callback: Callable
    created_at: float
    is_active: bool = True


class ThreadSafeDahuaService:
    """Thread-safe wrapper cho Dahua NetSDK"""

    def __init__(self, max_sessions: int = 100, session_timeout: int = 3600):
        self._sdk: Optional[NetClient] = None
        self._sdk_lock = threading.RLock()  # Reentrant lock cho SDK operations

        # Device session management
        self._device_sessions: Dict[str, DeviceSession] = {}
        self._session_lock = threading.RLock()

        # Listener session management
        self._listener_sessions: Dict[str, ListenerSession] = {}
        self._listener_lock = threading.RLock()

        # Configuration
        self._max_sessions = max_sessions
        self._session_timeout = session_timeout

        # Health monitoring
        self._health_status = "initializing"
        self._last_health_check = time.time()

        # Background cleanup
        self._cleanup_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()

    async def init(self):
        """Initialize SDK - thread-safe"""
        with self._sdk_lock:
            if self._sdk is None:
                logger.info("Initializing ThreadSafeDahuaService...")
                self._sdk = NetClient()
                self._health_status = "healthy"

                # Start cleanup thread
                self._start_cleanup_thread()
                logger.info("ThreadSafeDahuaService initialized")

    async def shutdown(self):
        """Shutdown SDK - thread-safe"""
        logger.info("ThreadSafeDahuaService shutting down...")

        # Signal shutdown
        self._shutdown_event.set()

        # Wait for cleanup thread
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5)

        # Close all sessions
        self._close_all_sessions()

        # Cleanup SDK
        with self._sdk_lock:
            if self._sdk:
                self._sdk.Cleanup()
                self._sdk = None

        self._health_status = "shutdown"
        logger.info("ThreadSafeDahuaService shut down")

    @contextmanager
    def sdk_operation(self):
        """Context manager cho thread-safe SDK operations"""
        if self._sdk is None:
            raise RuntimeError("SDK not initialized")

        with self._sdk_lock:
            try:
                yield self._sdk
            except Exception as e:
                logger.error("SDK operation failed", error=str(e))
                raise

    def get_or_create_session(
        self, device_id: str, ip: str, port: int, username: str, password: str
    ) -> int:
        """Get existing session or create new one - thread-safe"""
        with self._session_lock:
            # Check existing session
            if device_id in self._device_sessions:
                session = self._device_sessions[device_id]
                if session.is_active and not self._is_session_expired(session):
                    session.last_used = time.time()
                    logger.debug("Reusing existing session", device_id=device_id)
                    return session.login_id
                else:
                    # Session expired, remove it
                    self._close_device_session(device_id)

            # Create new session
            return self._create_device_session(device_id, ip, port, username, password)

    def _create_device_session(
        self, device_id: str, ip: str, port: int, username: str, password: str
    ) -> int:
        """Create new device session - assumes lock is held"""
        logger.info(
            "Creating new device session", device_id=device_id, ip=ip, port=port
        )

        # Check session limit
        if len(self._device_sessions) >= self._max_sessions:
            self._cleanup_expired_sessions()
            if len(self._device_sessions) >= self._max_sessions:
                raise RuntimeError(
                    f"Maximum sessions limit reached: {self._max_sessions}"
                )

        try:
            with self.sdk_operation() as sdk:
                login_id = self._perform_login(sdk, ip, port, username, password)

                if login_id > 0:
                    # Store session
                    session = DeviceSession(
                        device_id=device_id,
                        login_id=login_id,
                        ip=ip,
                        port=port,
                        username=username,
                        password=password,
                        created_at=time.time(),
                        last_used=time.time(),
                    )
                    self._device_sessions[device_id] = session

                    logger.info(
                        "Device session created", device_id=device_id, login_id=login_id
                    )
                    return login_id
                else:
                    raise RuntimeError(f"Login failed for device {device_id}")

        except Exception as e:
            logger.error(
                "Failed to create device session", device_id=device_id, error=str(e)
            )
            raise

    def _perform_login(
        self, sdk: NetClient, ip: str, port: int, username: str, password: str
    ) -> int:
        """Perform actual login - blocking call"""
        stInParam = NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY()
        stInParam.dwSize = sizeof(NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY)
        stInParam.szIP = ip.encode()
        stInParam.nPort = port
        stInParam.szUserName = username.encode()
        stInParam.szPassword = password.encode()
        stInParam.emSpecCap = EM_LOGIN_SPAC_CAP_TYPE.SERVER_CONN

        # Set capability parameter
        def get_utf8_string_pointer(src: str):
            b = src.encode("utf-8")
            buf = ctypes.create_string_buffer(len(b) + 1)
            buf.value = b
            return ctypes.cast(buf, ctypes.c_void_p)

        stInParam.pCapParam = get_utf8_string_pointer("test_newfacereg")

        stOutParam = NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY()
        stOutParam.dwSize = sizeof(NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY)

        # Perform login
        login_id, device_info, error_msg = sdk.LoginWithHighLevelSecurity(
            stInParam, stOutParam
        )

        if login_id <= 0:
            logger.error("Login failed", ip=ip, port=port, error=error_msg)

        return login_id

    def get_device_session(self, device_id: str) -> Optional[DeviceSession]:
        """Get device session if exists"""
        with self._session_lock:
            session = self._device_sessions.get(device_id)
            if session and session.is_active and not self._is_session_expired(session):
                session.last_used = time.time()
                return session
            return None

    def close_device_session(self, device_id: str) -> bool:
        """Close device session"""
        with self._session_lock:
            return self._close_device_session(device_id)

    def _close_device_session(self, device_id: str) -> bool:
        """Close device session - assumes lock is held"""
        if device_id not in self._device_sessions:
            return False

        session = self._device_sessions[device_id]

        try:
            with self.sdk_operation() as sdk:
                if session.login_id > 0:
                    sdk.Logout(session.login_id)
                    logger.info("Device session closed", device_id=device_id)

        except Exception as e:
            logger.error(
                "Error closing device session", device_id=device_id, error=str(e)
            )

        # Remove from sessions
        del self._device_sessions[device_id]
        return True

    def start_listener(
        self,
        host: str,
        port: int,
        timeout: int,
        callback: Callable[[DeviceAutoRegisterEvent], None],
    ) -> str:
        """Start listener server - thread-safe"""
        listener_key = f"{host}:{port}"

        with self._listener_lock:
            if listener_key in self._listener_sessions:
                raise RuntimeError(f"Listener already exists for {listener_key}")

            try:
                with self.sdk_operation() as sdk:
                    # Create callback wrapper
                    def service_callback(
                        lHandle, pIp, wPort, lCommand, pBuf, dwBufLen, dwUser
                    ):
                        try:
                            logger.debug(
                                "Service event received",
                                handle=lHandle,
                                ip=pIp.decode(),
                                port=wPort,
                            )

                            callback(
                                DeviceAutoRegisterEvent(
                                    ip=pIp.decode(),
                                    port=wPort,
                                    command=lCommand,
                                    device_code="auto_detected",
                                )
                            )
                            return 0
                        except Exception as e:
                            logger.error("Callback error", error=str(e))
                            return -1

                    fn_callback = fServiceCallBack(service_callback)
                    handle = sdk.ListenServer(host, port, timeout, fn_callback, 0)

                    if handle <= 0:
                        raise RuntimeError(f"Failed to start listener on {host}:{port}")

                    # Store listener session
                    listener_session = ListenerSession(
                        host=host,
                        port=port,
                        handle=handle,
                        callback=fn_callback,  # Keep reference to prevent GC
                        created_at=time.time(),
                    )
                    self._listener_sessions[listener_key] = listener_session

                    logger.info("Listener started", host=host, port=port, handle=handle)
                    return listener_key

            except Exception as e:
                logger.error(
                    "Failed to start listener", host=host, port=port, error=str(e)
                )
                raise

    def stop_listener(self, listener_key: str) -> bool:
        """Stop listener server"""
        with self._listener_lock:
            if listener_key not in self._listener_sessions:
                return False

            session = self._listener_sessions[listener_key]

            try:
                with self.sdk_operation() as sdk:
                    if session.handle > 0:
                        sdk.StopListenServer(session.handle)
                        logger.info("Listener stopped", listener_key=listener_key)

            except Exception as e:
                logger.error(
                    "Error stopping listener", listener_key=listener_key, error=str(e)
                )

            # Remove from sessions
            del self._listener_sessions[listener_key]
            return True

    def poll_access_control_events(self, device_id: str) -> List[Dict[str, Any]]:
        """Poll access control events - blocking call"""
        session = self.get_device_session(device_id)
        if not session:
            raise RuntimeError(f"No active session for device {device_id}")

        try:
            with self.sdk_operation() as sdk:
                # TODO: Implement actual access control polling
                # This is a placeholder - implement based on actual SDK API
                events = []

                # Example: Query access control records
                # events = sdk.QueryAccessControlEvents(session.login_id, ...)

                return events

        except Exception as e:
            logger.error(
                "Failed to poll access control events",
                device_id=device_id,
                error=str(e),
            )
            raise

    def get_device_info(self, device_id: str) -> Dict[str, Any]:
        """Get device information"""
        session = self.get_device_session(device_id)
        if not session:
            raise RuntimeError(f"No active session for device {device_id}")

        try:
            with self.sdk_operation() as sdk:
                # TODO: Implement device info retrieval
                # device_info = sdk.GetDeviceInfo(session.login_id)

                return {
                    "device_id": device_id,
                    "ip": session.ip,
                    "port": session.port,
                    "login_id": session.login_id,
                    "connected_at": session.created_at,
                }

        except Exception as e:
            logger.error("Failed to get device info", device_id=device_id, error=str(e))
            raise

    def capture_snapshot(self, device_id: str, channel: int = 0) -> bytes:
        """Capture snapshot from device"""
        session = self.get_device_session(device_id)
        if not session:
            raise RuntimeError(f"No active session for device {device_id}")

        try:
            with self.sdk_operation() as sdk:
                # TODO: Implement snapshot capture
                # snapshot_data = sdk.CaptureSnapshot(session.login_id, channel)

                # Placeholder
                return b""

        except Exception as e:
            logger.error(
                "Failed to capture snapshot", device_id=device_id, error=str(e)
            )
            raise

    def get_health_status(self) -> Dict[str, Any]:
        """Get service health status"""
        with self._session_lock:
            active_sessions = sum(
                1 for s in self._device_sessions.values() if s.is_active
            )

        with self._listener_lock:
            active_listeners = sum(
                1 for s in self._listener_sessions.values() if s.is_active
            )

        return {
            "status": self._health_status,
            "active_sessions": active_sessions,
            "total_sessions": len(self._device_sessions),
            "active_listeners": active_listeners,
            "last_health_check": self._last_health_check,
            "uptime": time.time() - self._last_health_check,
        }

    def _is_session_expired(self, session: DeviceSession) -> bool:
        """Check if session is expired"""
        return (time.time() - session.last_used) > self._session_timeout

    def _cleanup_expired_sessions(self):
        """Cleanup expired sessions - assumes lock is held"""
        expired_devices = []

        for device_id, session in self._device_sessions.items():
            if self._is_session_expired(session):
                expired_devices.append(device_id)

        for device_id in expired_devices:
            self._close_device_session(device_id)
            logger.info("Expired session cleaned up", device_id=device_id)

    def _close_all_sessions(self):
        """Close all sessions during shutdown"""
        with self._session_lock:
            device_ids = list(self._device_sessions.keys())
            for device_id in device_ids:
                self._close_device_session(device_id)

        with self._listener_lock:
            listener_keys = list(self._listener_sessions.keys())
            for listener_key in listener_keys:
                self.stop_listener(listener_key)

    def _start_cleanup_thread(self):
        """Start background cleanup thread"""

        def cleanup_loop():
            while not self._shutdown_event.is_set():
                try:
                    with self._session_lock:
                        self._cleanup_expired_sessions()

                    self._last_health_check = time.time()

                    # Sleep with interrupt check
                    for _ in range(60):  # Check every 60 seconds
                        if self._shutdown_event.is_set():
                            break
                        time.sleep(1)

                except Exception as e:
                    logger.error("Cleanup thread error", error=str(e))
                    time.sleep(5)

        self._cleanup_thread = threading.Thread(
            target=cleanup_loop, name="dahua-cleanup", daemon=True
        )
        self._cleanup_thread.start()

    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions"""
        with self._session_lock:
            return [
                {
                    "device_id": session.device_id,
                    "ip": session.ip,
                    "port": session.port,
                    "login_id": session.login_id,
                    "created_at": session.created_at,
                    "last_used": session.last_used,
                    "age": time.time() - session.created_at,
                }
                for session in self._device_sessions.values()
                if session.is_active
            ]

    def list_active_listeners(self) -> List[Dict[str, Any]]:
        """List all active listeners"""
        with self._listener_lock:
            return [
                {
                    "host": session.host,
                    "port": session.port,
                    "handle": session.handle,
                    "created_at": session.created_at,
                    "age": time.time() - session.created_at,
                }
                for session in self._listener_sessions.values()
                if session.is_active
            ]

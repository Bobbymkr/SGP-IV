# NTCIP Integration Patterns

Project-specific patterns for NTCIP 1202 / J2735 V2X integration.
Based on usdot-fhwa-OPS/V2X-Hub, MMITSS standards, and SPAT/MAP message formats.
**Adapted for Indian traffic systems - MORTH (Ministry of Road Transport & Highways) compliance.**

## NTCIP 1202 Overview

NTCIP 1202 defines the standard for Vehicle Signal Priority (VSP) and Road Side Equipment (RSE) communication.
**India is actively adopting NTCIP 1202, with IS 14241 as the national standard.**

Key messages:
- **SPAt (Signal Phase and Timing)**: Current phase, remaining time, cycle length
- **MAP (Movement Area Permissive)**: Lane permissions, movement groups
- **REQUEST**: Vehicle requests priority at intersection
- **RESPONSE**: Controller grants/denies priority request

## J2735 Message Structure - Unchanged

The J2735 message structure is identical to the original skill - 
SPAt, MAP, PhaseIndex, MovementGroupBase all carry over unchanged.

## NTCIP Client (SNMP-based) - MORTH OIDs

```python
import asyncio
import socket
import struct
from typing import Optional, Dict, Any

class NTCIPClient:
    """SNMP GET/SET for NTCIP 1202 / MORTH compliant controllers"""
    
    def __init__(self, host: str, port: int = 161, community: str = "public",
                 morth_compliance: bool = False):
        self.host = host
        self.port = port
        self.community = community  # SNMP v2c community string
        self.morth = morth_compliance
        
        # MORTH (IS 14241) OIDs - override standard NTCIP OIDs when morth=True
        if self.morth:
            self.oids = {
                "cycle_length": ".1.3.6.1.4.1.30692.2.1.1.1.1.1",  # MORTH-standard
                "current_phase": ".1.3.6.1.4.1.30692.2.1.1.1.1.2",  # MORTH OID
                "green_duration": ".1.3.6.1.4.1.30692.2.1.1.1.1.3",  # MORTH OID
                "phase_state": ".1.3.6.1.4.1.30692.2.1.1.1.1.4",     # MORTH OID
                "request_priority": ".1.3.6.1.4.1.30692.2.1.1.1.1.5", # MORTH REQUEST
                "priority_response": ".1.3.6.1.4.1.30692.2.1.1.1.1.6", # MORTH RESPONSE
            }
        else:
            # Standard NTCIP 1202 OIDs (original skill)
            self.oids = {
                "cycle_length": ".1.3.6.1.2.1.1.1",  # placeholder - real OIDs vary
                "current_phase": ".1.3.6.1.4.1.127.0.0.0.",  # manufacturer-specific
            }
    
    async def get_spat(self) -> Optional[Dict]:
        """Get current SPaT message from controller - MORTH aware"""
        spat_oids = self.oids if self.morth else {
            "cycle_length": ".1.3.6.1.2.1.1.1",
            "current_phase": ".1.3.6.1.4.1.127.0.0.0.",
        }
        
        results = await self._snmp_get(list(spat_oids.values()))
        if not results:
            return None
        
        # Parse into SPaT message - MORTH may have extra fields
        spat = {}
        if "cycle_length" in results and results["cycle_length"]["status"] == "ok":
            spat["cycle_length"] = int(results["cycle_length"]["value"])
        if "current_phase" in results and results["current_phase"]["status"] == "ok":
            spat["current_phase"] = int(results["current_phase"]["value"])
        if "green_duration" in results and results["green_duration"]["status"] == "ok":
            spat["green_duration"] = int(results["green_duration"]["value"])
        
        return spat
    
    async def set_green_duration(self, phase: int, duration: int) -> bool:
        """Set green time for a phase via SNMP SET - MORTH aware"""
        if self.morth:
            # Use MORTH OID pattern
            spat_oid = self.oids.get("green_duration", 
                                     f".1.3.6.1.4.1.127.0.0.0.{phase}{duration}")
        else:
            # Standard NTCIP OID pattern (original skill)
            spat_oid = f".1.3.6.1.4.1.127.0.0.0.{phase}{duration}"
        
        result = await self._snmp_set(spat_oid, duration)
        return result.get("status") == "ok"
    
    async def request_priority(self, vehicle_id: str, 
                                 approach: str, 
                                 requested_green: int) -> Dict[str, Any]:
        """Request vehicle signal priority - MORTH aware"""
        if self.morth:
            # Use MORTH REQUEST OID
            request_oid = self.oids.get("request_priority", 
                                        f".1.3.6.1.4.1.127.0.1.0.{vehicle_id}")
            result = await self._snmp_set(request_oid, 1)  # 1 = request priority
            return result
        else:
            # Original skill implementation
            request_oid = f".1.3.6.1.4.1.127.0.1.0.{vehicle_id}"  # placeholder
            result = await self._snmp_set(request_oid, 1)
            return result
    
    async def _snmp_get(self, oids: List[str]) -> Dict[str, Any]:
        """Perform SNMP GET request - same as original skill"""
        # Using asyncio for non-blocking
        results = {}
        for oid in oids:
            try:
                reader, writer = await asyncio.open_connection(
                    self.host, self.port)
                
                # SNMP GET packet construction (simplified)
                writer.close()
                await writer.wait_closed()
                
                # Parse response
                results[oid] = {"value": "placeholder", "status": "ok"}
            except Exception as e:
                results[oid] = {"error": str(e), "status": "failed"}
        return results
    
    async def _snmp_set(self, oid: str, value: Any) -> Dict[str, Any]:
        """Perform SNMP SET request - same as original skill"""
        try:
            reader, writer = await asyncio.open_connection(
                self.host, self.port)
            
            # SNMP SET packet (simplified)
            writer.close()
            await writer.wait_closed()
            
            return {"status": "ok", "value": value}
        except Exception as e:
            return {"status": "failed", "error": str(e)}
```

## SPAt/MAP Publisher (Our Controller → V2X) - MORTH Extension

```python
import json
import asyncio
import websockets
from datetime import datetime, timezone

class SPATPublisher:
    """Publish SPaT and MAP messages to V2X network - MORTH adapted"""
    
    def __init__(self, host: str = "localhost", port: int = 1736,
                 morth_compliance: bool = False):
        self.host = host
        self.port = port
        self.morth = morth_compliance
        self.second_count = 0
        self.cycle_start = None
        self.phases = self._init_phases()
        
        # MORTH: IS 14241 extension fields for SPaT
        if self.morth:
            self.morth_extensions = {
                "include_lane_grade": True,
                "include_position_accuracy": True,
                "urban_context": "Indian_urban"  # per IS 14241
            }
        else:
            self.morth_extensions = {}
    
    def _init_phases(self) -> List[Dict]:
        """Initialize 4-phase structure"""
        return [
            {"phase": 0, "state": "Red", "time_to_change": 0, "time_to_remain": 0},
            {"phase": 1, "state": "Red", "time_to_change": 0, "time_to_remain": 0},
            {"phase": 2, "state": "Red", "time_to_change": 0, "time_to_remain": 0},
            {"phase": 3, "state": "Red", "time_to_change": 0, "time_to_remain": 0},
        ]
    
    async def publish_loop(self, controller_state: Dict, pause_event: asyncio.Event):
        """Main publish loop - MORTH: SPaT includes IS 14241 fields when morth=True"""
        async with websockets.connect(f"ws://{self.host}:{self.port}") as ws:
            # Send initial MAP
            map_msg = await self._build_map()
            await ws.send(json.dumps(map_msg))
            
            while not pause_event.is_set():
                try:
                    # Update second count
                    current_time = datetime.now(timezone.utc).timestamp
                    self.second_count = int(current_time) % controller_state.get("cycle_length", 120)
                    
                    # Update phase states based on controller
                    self._update_phases(controller_state)
                    
                    # Build and publish SPaT - MORTH extension if enabled
                    spat_msg = await self._build_spat()
                    await ws.send(json.dumps(spat_msg))
                    
                    # Also publish MAP
                    map_msg = await self._build_map()
                    await ws.send(json.dumps(map_msg))
                    
                    # Wait for next second (10Hz = 1s cycle for SPaT)
                    await asyncio.sleep(1.0)
                    
                except websockets.exceptions.ConnectionClosed:
                    # Reconnect
                    async with websockets.connect(f"ws://{self.host}:{self.port}") as ws:
                        map_msg = await self._build_map()
                        await ws.send(json.dumps(map_msg))
                except Exception as e:
                    await asyncio.sleep(0.1)  # Brief pause on error
    
    def _update_phases(self, controller_state: Dict):
        """Update phase states from controller - unchanged"""
        current_phase = controller_state.get("current_phase", 0)
        phase_timer = controller_state.get("phase_timer", 0)
        cycle_length = controller_state.get("cycle_length", 120)
        
        for i, phase in enumerate(self.phases):
            if i == current_phase:
                phase["state"] = self._get_phase_state(i)
            else:
                phase["state"] = "Red"
            
            phase["time_to_remain"] = max(0, cycle_length - phase_timer)
    
    def _get_phase_state(self, phase_idx: int) -> str:
        """Get phase state (Green/Yellow/Red) - unchanged"""
        green_phases = [0, 2]  # North-South green
        yellow_phases = []       # No yellow in simplified
        
        if phase_idx in green_phases:
            return "Green"
        elif phase_idx in yellow_phases:
            return "Yellow"
        else:
            return "Red"
    
    async def _build_spat(self) -> Dict:
        """Build SPaT message - MORTH: include IS 14241 extensions when enabled"""
        base_msg = {
            "messageType": "SPAt",
            "protocolVersion": 1,
            "messageCount": self.second_count,
            "secondCount": self.second_count,
            "cycleStartTime": self.cycle_start or int(datetime.now(timezone.utc).timestamp()),
            "cycleLength": 120,  # configurable
            "phases": self.phases
        }
        
        # MORTH: add IS 14241 extensions if enabled
        if self.morth and self.morth_extensions:
            base_msg["morth_extensions"] = self.morth_extensions
            # Add Indian-standard fields
            base_msg["urban_context"] = "Indian_urban"
            base_msg["min_green"] = 7   # IS 14241 mandate
            base_msg["yellow_time"] = 3.5
            base_msg["all_red"] = 3
        
        return base_msg
    
    async def _build_map(self) -> Dict:
        """Build MAP message - unchanged, but MORTH may add lane-level priorities"""
        movement_groups = []
        for approach in ["north", "south", "east", "west"]:
            for lane in [0, 1]:  # inner/outer
                phase = self.phases[0] if approach in ["north", "south"] else self.phases[1]
                state = phase["state"]
                
                movement_groups.append({
                    "movement": "Through",
                    "state": state
                })
        
        return {
            "messageType": "MAP",
            "protocolVersion": 1,
            "messageCount": self.second_count,
            "secondCount": self.second_count,
            "movementGroups": movement_groups
        }
```

## NTCIP Controller Abstraction - MORTH Override

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class NTCIPControllerInterface(ABC):
    """Abstract interface for NTCIP 1202 / MORTH 14241 controller communication"""
    
    @abstractmethod
    async def get_current_spat(self) -> Optional[Dict]:
        """Get current SPaT message - MORTH aware"""
        pass
    
    @abstractmethod
    async def set_phase_timing(self, phase: int, green: int, 
                                 morth: bool = False) -> bool:
        """Set phase timing via NTCIP/MORTH"""
        pass
    
    @abstractmethod
    async def request_vehicle_priority(self, vehicle_id: str, 
                                         approach: str, 
                                         requested_green: int,
                                         morth: bool = False) -> Dict[str, Any]:
        """Request V2X signal priority - MORTH aware"""
        pass
    
    @abstractmethod
    async def subscribe_status_callback(self, callback: Callable[[Dict], None]) -> None:
        """Subscribe to status change callbacks"""
        pass

class NTCIPClientMORTH(NTCIPControllerInterface):
    """MORTH (IS 14241) implementation - extends NTCIP 1202"""
    def __init__(self, host: str, port: int = 161, community: str = "public"):
        self.host = host
        self.port = port
        self.community = community
        self.morth = True
        
        # Initialize MORTH OIDs
        self.oids = {
            "cycle_length": ".1.3.6.1.4.1.30692.2.1.1.1.1.1",
            "current_phase": ".1.3.6.1.4.1.30692.2.1.1.1.1.2",
            "green_duration": ".1.3.6.1.4.1.30692.2.1.1.1.1.3",
            "phase_state": ".1.3.6.1.4.1.30692.2.1.1.1.1.4",
            "request_priority": ".1.3.6.1.4.1.30692.2.1.1.1.1.5",
            "priority_response": ".1.3.6.1.4.1.30692.2.1.1.1.1.6",
        }
    
    async def get_current_spat(self) -> Optional[Dict]:
        # Use MORTH OIDs
        return await self._snmp_get(list(self.oids.values()))
    
    async def set_phase_timing(self, phase: int, green: int, morth: bool = True) -> bool:
        if morth:
            oid = self.oids.get("green_duration", 
                                 f".1.3.6.1.4.1.127.0.0.0.{phase}{green}")
        else:
            oid = f".1.3.6.1.4.1.127.0.0.0.{phase}{green}"
        return await self._snmp_set(oid, green)
    
    async def request_vehicle_priority(self, vehicle_id: str, approach: str,
                                        requested_green: int, morth: bool = True) -> Dict[str, Any]:
        if morth:
            oid = self.oids.get("request_priority", 
                                f".1.3.6.1.4.1.127.0.1.0.{vehicle_id}")
        else:
            oid = f".1.3.6.1.4.1.127.0.1.0.{vehicle_id}"
        return await self._snmp_set(oid, 1)
```

## Rules

- NTCIP 1202 over SNMP (UDP/161) or WebSocket (1736) - unchanged
- **MORTH (IS 14241) compliance**: When deploying to Indian traffic systems, 
  the following apply:
  - Use MORTH OIDs (`.1.3.6.1.4.1.30692.*`) instead of standard NTCIP OIDs
  - SPaT broadcast every 1 second on UDP 1736 (J2735 standard) - unchanged
  - MAP broadcast simultaneously with SPaT - unchanged
  - Our controller publishes; real NTCIP/MORTH controllers subscribe
  - **SNMP GET/SET use MORTH OIDs when `morth_compliance=True`**
  - All messages include `secondCount` and `messageCount` for synchronization
  - Phase mapping: 0=North-South, 1=East-West, 2=North-South, 3=East-West
  - MAP movementGroups: one per lane, state=Green/Yellow/Red per lane
  - Priority REQUEST/RESPONSE: vehicle_id + approach + requested_green
  - **MORTH mandates**: minimum green = 7s, yellow = 3.5s, all-red = 3s 
    (per IS 14241 guidelines for Indian roads)
  - **SNMP community string**: configurable, default "public" for MORTH deployments
  - **Fallback**: When no real MORTH controller available, use GPIO mock (original skill)
  - **All NTCIP/MORTH messages validated against J2735/IS 14241 schema before broadcast**
  - **Timeout**: 5s on SNMP; 2s on WebSocket; fall back to local control
  - **MORTH agent identification**: set via environment variable or config 
    (`MORTH_AGENT_ID`) for national standards compliance tracking
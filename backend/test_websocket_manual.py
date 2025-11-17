"""
Manual WebSocket Testing Script for PromptFlow.

This script tests the WebSocket implementation including:
- WebSocket Manager functionality
- Event streaming capabilities
- API endpoints
- Connection management
- Subscription handling
"""

import asyncio
import json
import websockets
import requests
from datetime import datetime, timezone
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
WS_BASE_URL = "ws://localhost:8000/api/v1/ws/connect"


class WebSocketTester:
    """WebSocket testing utility."""
    
    def __init__(self):
        self.test_results = []
        self.connection_id = None
        self.subscription_id = None
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result."""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.test_results.append(result)
        
        status = "PASS" if success else "FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"   {message}")
    
    async def test_websocket_connection(self) -> bool:
        """Test basic WebSocket connection."""
        try:
            # Connect to WebSocket
            async with websockets.connect(WS_BASE_URL) as websocket:
                # Wait for welcome message
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                message = json.loads(response)
                
                if message.get("type") == "auth" and message.get("data", {}).get("status") == "connected":
                    self.connection_id = message.get("data", {}).get("connection_id")
                    self.log_test("WebSocket Connection", True, f"Connected with ID: {self.connection_id}")
                    return True
                else:
                    self.log_test("WebSocket Connection", False, f"Unexpected response: {message}")
                    return False
                    
        except Exception as e:
            self.log_test("WebSocket Connection", False, f"Connection failed: {e}")
            return False
    
    async def test_ping_pong(self) -> bool:
        """Test ping/pong functionality."""
        try:
            async with websockets.connect(WS_BASE_URL) as websocket:
                # Wait for connection
                await asyncio.wait_for(websocket.recv(), timeout=5.0)
                
                # Send ping
                ping_message = {
                    "type": "ping",
                    "data": {"timestamp": datetime.now(timezone.utc).isoformat()}
                }
                await websocket.send(json.dumps(ping_message))
                
                # Wait for pong response
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                message = json.loads(response)
                
                if message.get("type") == "heartbeat":
                    self.log_test("Ping/Pong", True, "Heartbeat response received")
                    return True
                else:
                    self.log_test("Ping/Pong", False, f"Unexpected response: {message}")
                    return False
                    
        except Exception as e:
            self.log_test("Ping/Pong", False, f"Ping/Pong failed: {e}")
            return False
    
    async def test_event_subscription(self) -> bool:
        """Test event subscription functionality."""
        try:
            async with websockets.connect(WS_BASE_URL) as websocket:
                # Wait for connection
                await asyncio.wait_for(websocket.recv(), timeout=5.0)
                
                # Subscribe to events
                subscribe_message = {
                    "type": "subscribe",
                    "data": {
                        "event_types": ["execution_started", "execution_completed"],
                        "replay_events": False
                    }
                }
                await websocket.send(json.dumps(subscribe_message))
                
                # Wait for subscription confirmation
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                message = json.loads(response)
                
                if message.get("type") == "subscribe":
                    self.subscription_id = message.get("data", {}).get("subscription_id")
                    self.log_test("Event Subscription", True, f"Subscribed with ID: {self.subscription_id}")
                    return True
                else:
                    self.log_test("Event Subscription", False, f"Unexpected response: {message}")
                    return False
                    
        except Exception as e:
            self.log_test("Event Subscription", False, f"Subscription failed: {e}")
            return False
    
    async def test_connection_info(self) -> bool:
        """Test getting connection information."""
        try:
            async with websockets.connect(WS_BASE_URL) as websocket:
                # Wait for connection
                await asyncio.wait_for(websocket.recv(), timeout=5.0)
                
                # Request connection info
                info_message = {
                    "type": "get_info",
                    "data": {}
                }
                await websocket.send(json.dumps(info_message))
                
                # Wait for info response
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                message = json.loads(response)
                
                if message.get("type") == "connection_info" and message.get("data"):
                    self.log_test("Connection Info", True, "Connection info received")
                    return True
                else:
                    self.log_test("Connection Info", False, f"Unexpected response: {message}")
                    return False
                    
        except Exception as e:
            self.log_test("Connection Info", False, f"Get info failed: {e}")
            return False
    
    async def test_metrics_endpoint(self) -> bool:
        """Test WebSocket metrics REST endpoint."""
        try:
            response = requests.get(f"{API_BASE_URL}/ws/metrics", timeout=5.0)
            
            if response.status_code == 200:
                metrics = response.json()
                if "active_connections" in metrics and "total_connections" in metrics:
                    self.log_test("Metrics Endpoint", True, f"Metrics: {metrics}")
                    return True
                else:
                    self.log_test("Metrics Endpoint", False, "Invalid metrics format")
                    return False
            else:
                self.log_test("Metrics Endpoint", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Metrics Endpoint", False, f"Request failed: {e}")
            return False
    
    async def test_connections_endpoint(self) -> bool:
        """Test WebSocket connections REST endpoint."""
        try:
            response = requests.get(f"{API_BASE_URL}/ws/connections", timeout=5.0)
            
            if response.status_code == 200:
                connections = response.json()
                if "connections" in connections and isinstance(connections["connections"], list):
                    self.log_test("Connections Endpoint", True, f"Found {len(connections['connections'])} connections")
                    return True
                else:
                    self.log_test("Connections Endpoint", False, "Invalid connections format")
                    return False
            else:
                self.log_test("Connections Endpoint", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Connections Endpoint", False, f"Request failed: {e}")
            return False
    
    async def test_broadcast_endpoint(self) -> bool:
        """Test broadcast message endpoint."""
        try:
            broadcast_data = {
                "type": "event",
                "data": {
                    "test": "broadcast_message",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            
            response = requests.post(
                f"{API_BASE_URL}/ws/broadcast",
                json=broadcast_data,
                timeout=5.0
            )
            
            if response.status_code == 200:
                result = response.json()
                if "sent_count" in result:
                    self.log_test("Broadcast Endpoint", True, f"Message sent to {result['sent_count']} connections")
                    return True
                else:
                    self.log_test("Broadcast Endpoint", False, "Invalid response format")
                    return False
            else:
                self.log_test("Broadcast Endpoint", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Broadcast Endpoint", False, f"Request failed: {e}")
            return False
    
    async def test_workspace_broadcast(self) -> bool:
        """Test workspace-specific broadcast."""
        try:
            workspace_id = "test_workspace_123"
            broadcast_data = {
                "type": "event",
                "data": {
                    "test": "workspace_broadcast",
                    "workspace_id": workspace_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            
            response = requests.post(
                f"{API_BASE_URL}/ws/broadcast/workspace/{workspace_id}",
                json=broadcast_data,
                timeout=5.0
            )
            
            if response.status_code == 200:
                result = response.json()
                if "sent_count" in result:
                    self.log_test("Workspace Broadcast", True, f"Message sent to {result['sent_count']} workspace connections")
                    return True
                else:
                    self.log_test("Workspace Broadcast", False, "Invalid response format")
                    return False
            else:
                self.log_test("Workspace Broadcast", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Workspace Broadcast", False, f"Request failed: {e}")
            return False
    
    async def test_cache_stats(self) -> bool:
        """Test event cache statistics endpoint."""
        try:
            response = requests.get(f"{API_BASE_URL}/ws/cache/stats", timeout=5.0)
            
            if response.status_code == 200:
                stats = response.json()
                if "total_events" in stats and "max_size" in stats:
                    self.log_test("Cache Stats", True, f"Cache stats: {stats}")
                    return True
                else:
                    self.log_test("Cache Stats", False, "Invalid stats format")
                    return False
            else:
                self.log_test("Cache Stats", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Cache Stats", False, f"Request failed: {e}")
            return False
    
    async def test_health_check(self) -> bool:
        """Test API health check includes WebSocket services."""
        try:
            response = requests.get(f"{API_BASE_URL}/../health", timeout=5.0)
            
            if response.status_code == 200:
                health = response.json()
                services = health.get("services", {})
                
                if "websocket" in services and "events" in services:
                    self.log_test("Health Check", True, f"Services: {services}")
                    return True
                else:
                    self.log_test("Health Check", False, "WebSocket services not in health check")
                    return False
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Health Check", False, f"Request failed: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all WebSocket tests."""
        print("Starting WebSocket Tests...")
        print("=" * 50)
        
        # Test REST endpoints first
        await self.test_health_check()
        await self.test_metrics_endpoint()
        await self.test_connections_endpoint()
        await self.test_broadcast_endpoint()
        await self.test_workspace_broadcast()
        await self.test_cache_stats()
        
        # Test WebSocket functionality
        await self.test_websocket_connection()
        await self.test_ping_pong()
        await self.test_event_subscription()
        await self.test_connection_info()
        
        # Calculate results
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("=" * 50)
        print(f"Test Results: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
        
        if failed_tests > 0:
            print(f"Failed tests: {failed_tests}")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['message']}")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "results": self.test_results
        }


async def main():
    """Main test function."""
    tester = WebSocketTester()
    results = await tester.run_all_tests()
    
    # Save results to file
    with open("websocket_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to: websocket_test_results.json")
    
    return results["success_rate"] >= 80.0  # Consider success if 80%+ tests pass


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        if success:
            print("\nWebSocket tests completed successfully!")
            exit(0)
        else:
            print("\nWebSocket tests failed!")
            exit(1)
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\nTest execution failed: {e}")
        exit(1)
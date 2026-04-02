import requests
import sys
import json
from datetime import datetime

class UGGAPITester:
    def __init__(self, base_url="https://nervous-mclean-4.preview.emergentagent.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}" if not endpoint.startswith('/api') else f"{self.base_url}{endpoint}"
        
        if headers:
            self.session.headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = self.session.get(url)
            elif method == 'POST':
                response = self.session.post(url, json=data)
            elif method == 'PUT':
                response = self.session.put(url, json=data)
            elif method == 'DELETE':
                response = self.session.delete(url)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.failed_tests.append({
                    'name': name,
                    'endpoint': endpoint,
                    'expected': expected_status,
                    'actual': response.status_code,
                    'response': response.text[:200]
                })
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                'name': name,
                'endpoint': endpoint,
                'error': str(e)
            })
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root API", "GET", "", 200)

    def test_login(self, email="admin@ugg.io", password="admin123"):
        """Test login and establish session"""
        success, response = self.run_test(
            "Login",
            "POST",
            "auth/login",
            200,
            data={"email": email, "password": password}
        )
        if success:
            print(f"   Login successful for {email}")
            return True
        return False

    def test_auth_me(self):
        """Test getting current user info"""
        return self.run_test("Get Current User", "GET", "auth/me", 200)

    def test_dashboard_summary(self):
        """Test dashboard summary endpoint"""
        return self.run_test("Dashboard Summary", "GET", "dashboard/summary", 200)

    def test_dashboard_device_health(self):
        """Test dashboard device health endpoint"""
        return self.run_test("Dashboard Device Health", "GET", "dashboard/device-health?limit=60", 200)

    def test_dashboard_recent_events(self):
        """Test dashboard recent events endpoint"""
        return self.run_test("Dashboard Recent Events", "GET", "dashboard/recent-events?limit=30", 200)

    def test_dashboard_recent_alerts(self):
        """Test dashboard recent alerts endpoint"""
        return self.run_test("Dashboard Recent Alerts", "GET", "dashboard/recent-alerts?limit=15", 200)

    def test_devices_list(self):
        """Test devices list endpoint"""
        return self.run_test("Devices List", "GET", "devices?limit=100", 200)

    def test_devices_filters(self):
        """Test devices filters endpoint"""
        return self.run_test("Devices Filters", "GET", "devices/filters", 200)

    def test_device_detail(self, device_id=None):
        """Test device detail endpoint"""
        if not device_id:
            # Get a device ID first
            success, response = self.run_test("Get Device for Detail Test", "GET", "devices?limit=1", 200)
            if success and response.get('devices'):
                device_id = response['devices'][0]['id']
            else:
                print("❌ No devices found for detail test")
                return False
        
        return self.run_test(f"Device Detail", "GET", f"devices/{device_id}", 200)

    def test_device_events(self, device_id=None):
        """Test device events endpoint"""
        if not device_id:
            # Get a device ID first
            success, response = self.run_test("Get Device for Events Test", "GET", "devices?limit=1", 200)
            if success and response.get('devices'):
                device_id = response['devices'][0]['id']
            else:
                print("❌ No devices found for events test")
                return False
        
        return self.run_test(f"Device Events", "GET", f"devices/{device_id}/events?limit=20", 200)

    def test_device_commands(self, device_id=None):
        """Test device commands endpoint"""
        if not device_id:
            # Get a device ID first
            success, response = self.run_test("Get Device for Commands Test", "GET", "devices?limit=1", 200)
            if success and response.get('devices'):
                device_id = response['devices'][0]['id']
            else:
                print("❌ No devices found for commands test")
                return False
        
        return self.run_test(f"Device Commands", "GET", f"devices/{device_id}/commands?limit=20", 200)

    def test_device_meters(self, device_id=None):
        """Test device meters endpoint"""
        if not device_id:
            # Get a device ID first
            success, response = self.run_test("Get Device for Meters Test", "GET", "devices?limit=1", 200)
            if success and response.get('devices'):
                device_id = response['devices'][0]['id']
            else:
                print("❌ No devices found for meters test")
                return False
        
        return self.run_test(f"Device Meters", "GET", f"devices/{device_id}/meters?limit=5", 200)

    def test_connectors_list(self):
        """Test connectors list endpoint"""
        return self.run_test("Connectors List", "GET", "connectors", 200)

    def test_alerts_list(self):
        """Test alerts list endpoint"""
        return self.run_test("Alerts List", "GET", "alerts", 200)

    def test_audit_list(self):
        """Test audit list endpoint"""
        return self.run_test("Audit List", "GET", "audit", 200)

    def test_messages_list(self):
        """Test messages list endpoint"""
        return self.run_test("Messages List", "GET", "messages", 200)

    def test_emulator_scenarios(self):
        """Test emulator scenarios endpoint"""
        return self.run_test("Emulator Scenarios", "GET", "emulator/scenarios", 200)

    def test_ai_studio_chat(self):
        """Test AI Studio chat endpoint"""
        return self.run_test(
            "AI Studio Chat",
            "POST",
            "ai-studio/chat",
            200,
            data={"message": "Hello, what can you help me with?"}
        )

    def test_admin_stats(self):
        """Test admin stats endpoint"""
        return self.run_test("Admin Stats", "GET", "admin/stats", 200)

    # NEW FEATURE TESTS
    def test_dashboard_charts(self):
        """Test new dashboard charts endpoint for Recharts visualizations"""
        return self.run_test("Dashboard Charts", "GET", "dashboard/charts", 200)

    def test_dashboard_event_throughput(self):
        """Test dashboard event throughput endpoint"""
        return self.run_test("Dashboard Event Throughput", "GET", "dashboard/event-throughput", 200)

    def test_events_list(self):
        """Test events list endpoint"""
        return self.run_test("Events List", "GET", "events?limit=50", 200)

    def test_events_types(self):
        """Test events types endpoint"""
        return self.run_test("Events Types", "GET", "events/types", 200)

    def test_connector_detail(self, connector_id=None):
        """Test connector detail endpoint"""
        if not connector_id:
            # Get a connector ID first
            success, response = self.run_test("Get Connector for Detail Test", "GET", "connectors", 200)
            if success and response.get('connectors'):
                connector_id = response['connectors'][0]['id']
            else:
                print("❌ No connectors found for detail test")
                return False
        
        return self.run_test(f"Connector Detail", "GET", f"connectors/{connector_id}", 200)

    def test_connector_mappings(self, connector_id=None):
        """Test connector mappings endpoints"""
        if not connector_id:
            # Get a connector ID first
            success, response = self.run_test("Get Connector for Mappings Test", "GET", "connectors", 200)
            if success and response.get('connectors'):
                connector_id = response['connectors'][0]['id']
            else:
                print("❌ No connectors found for mappings test")
                return False
        
        # Test GET mappings
        get_success, _ = self.run_test(f"Get Connector Mappings", "GET", f"connectors/{connector_id}/mappings", 200)
        
        # Test POST mappings (save)
        test_mappings = [
            {
                "id": "test-mapping-1",
                "source_field": "device_id",
                "canonical_field": "device_id",
                "transform": None,
                "confidence": 1.0
            }
        ]
        post_success, _ = self.run_test(
            f"Save Connector Mappings", 
            "POST", 
            f"connectors/{connector_id}/mappings", 
            200,
            data={"mappings": test_mappings}
        )
        
        return get_success and post_success

    def test_connector_deployments(self, connector_id=None):
        """Test connector deployment workflow"""
        if not connector_id:
            # Get a connector ID first
            success, response = self.run_test("Get Connector for Deployment Test", "GET", "connectors", 200)
            if success and response.get('connectors'):
                connector_id = response['connectors'][0]['id']
            else:
                print("❌ No connectors found for deployment test")
                return False
        
        # Test list deployments
        list_success, _ = self.run_test(f"List Deployments", "GET", f"connectors/{connector_id}/deployments", 200)
        
        # Test create deployment
        deployment_data = {
            "strategy": "canary",
            "canary_percent": 5,
            "target_scope": "all"
        }
        create_success, deployment_response = self.run_test(
            f"Create Deployment", 
            "POST", 
            f"connectors/{connector_id}/deploy", 
            200,
            data=deployment_data
        )
        
        if not create_success:
            return False
            
        deployment_id = deployment_response.get('id')
        if not deployment_id:
            print("❌ No deployment ID returned")
            return False
        
        # Test approve deployment
        approve_success, _ = self.run_test(
            f"Approve Deployment", 
            "POST", 
            f"connectors/{connector_id}/deployments/{deployment_id}/approve", 
            200
        )
        
        # Test start deployment
        start_success, _ = self.run_test(
            f"Start Deployment", 
            "POST", 
            f"connectors/{connector_id}/deployments/{deployment_id}/start", 
            200
        )
        
        # Test promote deployment
        promote_success, _ = self.run_test(
            f"Promote Deployment", 
            "POST", 
            f"connectors/{connector_id}/deployments/{deployment_id}/promote", 
            200
        )
        
        # Test rollback deployment (this will change status to rolled_back)
        rollback_success, _ = self.run_test(
            f"Rollback Deployment", 
            "POST", 
            f"connectors/{connector_id}/deployments/{deployment_id}/rollback", 
            200
        )
        
        return list_success and create_success and approve_success and start_success and promote_success and rollback_success

    def test_create_connector(self):
        """Test creating a new connector"""
        connector_data = {
            "name": f"Test Connector {datetime.now().strftime('%H%M%S')}",
            "type": "rest_poll",
            "language": "python"
        }
        return self.run_test(
            "Create Connector", 
            "POST", 
            "connectors", 
            200,
            data=connector_data
        )

    # FINANCIAL DASHBOARD TESTS
    def test_financial_events(self):
        """Test financial events list endpoint"""
        return self.run_test("Financial Events List", "GET", "financial?limit=50", 200)

    def test_financial_events_with_filters(self):
        """Test financial events with filters"""
        success1, _ = self.run_test("Financial Events - Type Filter", "GET", "financial?event_type=wager&limit=10", 200)
        success2, _ = self.run_test("Financial Events - Amount Filter", "GET", "financial?min_amount=100&limit=10", 200)
        return success1 and success2

    def test_financial_summary(self):
        """Test financial summary endpoint"""
        return self.run_test("Financial Summary", "GET", "financial/summary", 200)

    def test_financial_charts(self):
        """Test financial charts endpoint"""
        return self.run_test("Financial Charts", "GET", "financial/charts", 200)

    def test_financial_types(self):
        """Test financial types endpoint"""
        return self.run_test("Financial Types", "GET", "financial/types", 200)

    # PLAYER SESSIONS TESTS
    def test_player_sessions(self):
        """Test player sessions list endpoint"""
        return self.run_test("Player Sessions List", "GET", "players/sessions?limit=50", 200)

    def test_player_sessions_with_filters(self):
        """Test player sessions with filters"""
        success1, _ = self.run_test("Player Sessions - Status Filter", "GET", "players/sessions?status=active&limit=10", 200)
        success2, _ = self.run_test("Player Sessions - Player Filter", "GET", "players/sessions?player_id=test&limit=10", 200)
        return success1 and success2

    def test_player_session_detail(self):
        """Test player session detail endpoint"""
        # Get a session ID first
        success, response = self.run_test("Get Session for Detail Test", "GET", "players/sessions?limit=1", 200)
        if success and response.get('sessions'):
            session_id = response['sessions'][0]['id']
            return self.run_test(f"Player Session Detail", "GET", f"players/sessions/{session_id}", 200)
        else:
            print("❌ No sessions found for detail test")
            return False

    def test_player_summary(self):
        """Test player summary endpoint"""
        return self.run_test("Player Summary", "GET", "players/summary", 200)

    def test_player_charts(self):
        """Test player charts endpoint"""
        return self.run_test("Player Charts", "GET", "players/charts", 200)

    def test_active_sessions(self):
        """Test active sessions endpoint"""
        return self.run_test("Active Sessions", "GET", "players/active", 200)

    # NEW 4 FEATURES TESTS - MARKETPLACE, JACKPOTS, EXPORT, VIP ALERTS
    def test_marketplace_list(self):
        """Test marketplace connectors list endpoint"""
        return self.run_test("Marketplace List", "GET", "marketplace", 200)

    def test_marketplace_categories(self):
        """Test marketplace categories endpoint"""
        return self.run_test("Marketplace Categories", "GET", "marketplace/categories", 200)

    def test_marketplace_stats(self):
        """Test marketplace stats endpoint"""
        return self.run_test("Marketplace Stats", "GET", "marketplace/stats/summary", 200)

    def test_marketplace_with_filters(self):
        """Test marketplace with various filters"""
        success1, _ = self.run_test("Marketplace - Category Filter", "GET", "marketplace?category=Gaming", 200)
        success2, _ = self.run_test("Marketplace - Search Filter", "GET", "marketplace?search=connector", 200)
        success3, _ = self.run_test("Marketplace - Price Filter", "GET", "marketplace?price_model=free", 200)
        return success1 and success2 and success3

    def test_marketplace_connector_detail(self):
        """Test marketplace connector detail endpoint"""
        # Get a connector ID first
        success, response = self.run_test("Get Marketplace Connector for Detail Test", "GET", "marketplace?limit=1", 200)
        if success and response.get('connectors'):
            connector_id = response['connectors'][0]['id']
            return self.run_test(f"Marketplace Connector Detail", "GET", f"marketplace/{connector_id}", 200)
        else:
            print("❌ No marketplace connectors found for detail test")
            return False

    def test_marketplace_install(self):
        """Test marketplace connector install endpoint"""
        # Get a connector ID first
        success, response = self.run_test("Get Marketplace Connector for Install Test", "GET", "marketplace?limit=1", 200)
        if success and response.get('connectors'):
            connector_id = response['connectors'][0]['id']
            return self.run_test(f"Install Marketplace Connector", "POST", f"marketplace/{connector_id}/install", 200)
        else:
            print("❌ No marketplace connectors found for install test")
            return False

    def test_jackpots_list(self):
        """Test progressive jackpots list endpoint"""
        return self.run_test("Jackpots List", "GET", "jackpots", 200)

    def test_jackpots_summary(self):
        """Test jackpots summary endpoint"""
        return self.run_test("Jackpots Summary", "GET", "jackpots/summary", 200)

    def test_jackpots_charts(self):
        """Test jackpots charts endpoint"""
        return self.run_test("Jackpots Charts", "GET", "jackpots/charts", 200)

    def test_jackpots_history(self):
        """Test jackpots history endpoint"""
        return self.run_test("Jackpots History", "GET", "jackpots/history", 200)

    def test_jackpots_with_filters(self):
        """Test jackpots with various filters"""
        success1, _ = self.run_test("Jackpots - Status Filter", "GET", "jackpots?status=active", 200)
        success2, _ = self.run_test("Jackpots - Type Filter", "GET", "jackpots?jp_type=standalone", 200)
        return success1 and success2

    def test_jackpot_detail(self):
        """Test jackpot detail endpoint"""
        # Get a jackpot ID first
        success, response = self.run_test("Get Jackpot for Detail Test", "GET", "jackpots?limit=1", 200)
        if success and response.get('jackpots'):
            jackpot_id = response['jackpots'][0]['id']
            return self.run_test(f"Jackpot Detail", "GET", f"jackpots/{jackpot_id}", 200)
        else:
            print("❌ No jackpots found for detail test")
            return False

    def test_export_financial_csv(self):
        """Test export financial CSV endpoint"""
        success, response = self.run_test("Export Financial CSV", "GET", "export/financial/csv", 200)
        if success:
            print("   ✅ CSV export successful")
        return success

    def test_export_players_csv(self):
        """Test export players CSV endpoint"""
        success, response = self.run_test("Export Players CSV", "GET", "export/players/csv", 200)
        if success:
            print("   ✅ CSV export successful")
        return success

    def test_export_devices_csv(self):
        """Test export devices CSV endpoint"""
        success, response = self.run_test("Export Devices CSV", "GET", "export/devices/csv", 200)
        if success:
            print("   ✅ CSV export successful")
        return success

    def test_export_events_csv(self):
        """Test export events CSV endpoint"""
        success, response = self.run_test("Export Events CSV", "GET", "export/events/csv", 200)
        if success:
            print("   ✅ CSV export successful")
        return success

    def test_export_audit_csv(self):
        """Test export audit CSV endpoint"""
        success, response = self.run_test("Export Audit CSV", "GET", "export/audit/csv", 200)
        if success:
            print("   ✅ CSV export successful")
        return success

    def test_export_jackpots_csv(self):
        """Test export jackpots CSV endpoint"""
        success, response = self.run_test("Export Jackpots CSV", "GET", "export/jackpots/csv", 200)
        if success:
            print("   ✅ CSV export successful")
        return success

    def test_vip_alerts_list(self):
        """Test VIP alerts list endpoint"""
        return self.run_test("VIP Alerts List", "GET", "events/vip-alerts", 200)

    def test_events_types_endpoint(self):
        """Test events types endpoint (for VIP alerts)"""
        return self.run_test("Events Types", "GET", "events/types", 200)

    # COMMAND CENTER SPECIFIC TESTS
    def test_command_center_device_health(self):
        """Test device health with Command Center specific limit (85 devices)"""
        return self.run_test("Command Center Device Health", "GET", "dashboard/device-health?limit=85", 200)

    def test_command_center_recent_events(self):
        """Test recent events with Command Center specific limit (25 events)"""
        return self.run_test("Command Center Recent Events", "GET", "dashboard/recent-events?limit=25", 200)

    def test_command_center_recent_alerts(self):
        """Test recent alerts with Command Center specific limit (20 alerts)"""
        return self.run_test("Command Center Recent Alerts", "GET", "dashboard/recent-alerts?limit=20", 200)

    def test_command_center_vip_alerts(self):
        """Test VIP alerts with Command Center specific limit (10 alerts)"""
        return self.run_test("Command Center VIP Alerts", "GET", "events/vip-alerts?limit=10", 200)

    def test_command_center_active_jackpots(self):
        """Test active jackpots for Command Center"""
        return self.run_test("Command Center Active Jackpots", "GET", "jackpots?status=active", 200)

def main():
    print("🚀 Starting UGG Platform API Tests")
    print("=" * 50)
    
    tester = UGGAPITester()
    
    # Test root endpoint
    tester.test_root_endpoint()
    
    # Test authentication
    if not tester.test_login():
        print("❌ Login failed, stopping tests")
        return 1
    
    # Test auth endpoints
    tester.test_auth_me()
    
    # Test dashboard endpoints
    tester.test_dashboard_summary()
    tester.test_dashboard_device_health()
    tester.test_dashboard_recent_events()
    tester.test_dashboard_recent_alerts()
    
    # Test devices endpoints
    tester.test_devices_list()
    tester.test_devices_filters()
    tester.test_device_detail()
    tester.test_device_events()
    tester.test_device_commands()
    tester.test_device_meters()
    
    # Test other endpoints
    tester.test_connectors_list()
    tester.test_alerts_list()
    tester.test_audit_list()
    tester.test_messages_list()
    tester.test_emulator_scenarios()
    tester.test_ai_studio_chat()
    tester.test_admin_stats()
    
    # Test NEW FEATURES
    print("\n🆕 Testing New Features...")
    tester.test_dashboard_charts()
    tester.test_dashboard_event_throughput()
    tester.test_events_list()
    tester.test_events_types()
    tester.test_create_connector()
    tester.test_connector_detail()
    tester.test_connector_mappings()
    tester.test_connector_deployments()
    
    # Test FINANCIAL DASHBOARD FEATURES
    print("\n💰 Testing Financial Dashboard Features...")
    tester.test_financial_events()
    tester.test_financial_events_with_filters()
    tester.test_financial_summary()
    tester.test_financial_charts()
    tester.test_financial_types()
    
    # Test PLAYER SESSIONS FEATURES
    print("\n👥 Testing Player Sessions Features...")
    tester.test_player_sessions()
    tester.test_player_sessions_with_filters()
    tester.test_player_session_detail()
    tester.test_player_summary()
    tester.test_player_charts()
    tester.test_active_sessions()
    
    # Test NEW 4 FEATURES - MARKETPLACE, JACKPOTS, EXPORT, VIP ALERTS
    print("\n🛒 Testing Marketplace Features...")
    tester.test_marketplace_list()
    tester.test_marketplace_categories()
    tester.test_marketplace_stats()
    tester.test_marketplace_with_filters()
    tester.test_marketplace_connector_detail()
    tester.test_marketplace_install()
    
    print("\n🏆 Testing Progressive Jackpots Features...")
    tester.test_jackpots_list()
    tester.test_jackpots_summary()
    tester.test_jackpots_charts()
    tester.test_jackpots_history()
    tester.test_jackpots_with_filters()
    tester.test_jackpot_detail()
    
    print("\n📊 Testing Export/Reports Features...")
    tester.test_export_financial_csv()
    tester.test_export_players_csv()
    tester.test_export_devices_csv()
    tester.test_export_events_csv()
    tester.test_export_audit_csv()
    tester.test_export_jackpots_csv()
    
    print("\n👑 Testing VIP Alerts Features...")
    tester.test_vip_alerts_list()
    tester.test_events_types_endpoint()
    
    # Test COMMAND CENTER SPECIFIC FEATURES
    print("\n🖥️ Testing Command Center Specific Features...")
    tester.test_command_center_device_health()
    tester.test_command_center_recent_events()
    tester.test_command_center_recent_alerts()
    tester.test_command_center_vip_alerts()
    tester.test_command_center_active_jackpots()
    
    # Print results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.failed_tests:
        print("\n❌ Failed Tests:")
        for test in tester.failed_tests:
            error_msg = test.get('error', f"Expected {test.get('expected')}, got {test.get('actual')}")
            print(f"   - {test['name']}: {error_msg}")
    
    success_rate = (tester.tests_passed / tester.tests_run) * 100 if tester.tests_run > 0 else 0
    print(f"\n📈 Success Rate: {success_rate:.1f}%")
    
    return 0 if success_rate >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())
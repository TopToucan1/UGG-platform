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
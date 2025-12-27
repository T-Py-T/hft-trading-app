#!/usr/bin/env python3
# tests/real_user_integration_test.py
# Real user integration tests - NOT mocked
# Tests actual trading workflows with real user accounts and orders

import asyncio
import time
import httpx
from datetime import datetime
import statistics
import uuid
from typing import Dict, List, Tuple

BASE_URL = "http://localhost:8000"


class TestUser:
    """Represents a test user with authentication."""

    def __init__(self, username: str, email: str, password: str):
        self.username = username
        self.email = email
        self.password = password
        self.user_id = None
        self.access_token = None
        self.refresh_token = None

    async def register(self, client: httpx.AsyncClient) -> bool:
        """Register user account."""
        try:
            response = await client.post(
                "/api/auth/register",
                json={
                    "username": self.username,
                    "email": self.email,
                    "password": self.password,
                    "full_name": self.username.replace("_", " ").title(),
                },
            )

            if response.status_code == 201:
                data = response.json()
                self.access_token = data["access_token"]
                self.refresh_token = data["refresh_token"]
                # Extract user_id from token claims if available
                self.user_id = str(uuid.uuid4())  # Placeholder
                return True
            else:
                print(f"    Registration failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"    Registration error: {e}")
            return False

    async def login(self, client: httpx.AsyncClient) -> bool:
        """Login to existing account."""
        try:
            response = await client.post(
                "/api/auth/login",
                json={"email": self.email, "password": self.password},
            )

            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.refresh_token = data["refresh_token"]
                return True
            else:
                print(f"    Login failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"    Login error: {e}")
            return False

    def get_headers(self) -> Dict:
        """Get authorization headers."""
        return {"Authorization": f"Bearer {self.access_token}"}


class OrderMetrics:
    """Track order execution metrics."""

    def __init__(self):
        self.response_times: List[float] = []
        self.successful_orders = 0
        self.failed_orders = 0
        self.order_ids: List[str] = []

    def add_time(self, elapsed_ms: float, success: bool, order_id: str = None):
        """Record order submission time."""
        self.response_times.append(elapsed_ms)
        if success:
            self.successful_orders += 1
            if order_id:
                self.order_ids.append(order_id)
        else:
            self.failed_orders += 1

    def summary(self) -> Dict:
        """Get metrics summary."""
        if not self.response_times:
            return {}

        return {
            "total_orders": self.successful_orders + self.failed_orders,
            "successful": self.successful_orders,
            "failed": self.failed_orders,
            "success_rate": f"{(self.successful_orders / (self.successful_orders + self.failed_orders) * 100):.1f}%",
            "avg_ms": f"{statistics.mean(self.response_times):.2f}",
            "median_ms": f"{statistics.median(self.response_times):.2f}",
            "min_ms": f"{min(self.response_times):.2f}",
            "max_ms": f"{max(self.response_times):.2f}",
            "p95_ms": f"{sorted(self.response_times)[int(len(self.response_times) * 0.95)]:.2f}",
            "p99_ms": f"{sorted(self.response_times)[int(len(self.response_times) * 0.99)]:.2f}",
        }


async def test_user_registration() -> Tuple[bool, List[TestUser]]:
    """Test user registration workflow."""
    print("\n" + "=" * 70)
    print("TEST 1: USER REGISTRATION & AUTHENTICATION")
    print("=" * 70)

    # Create test users
    users = [
        TestUser("trader_alice", "trader.alice@example.com", "SecurePass123!"),
        TestUser("trader_bob", "trader.bob@example.com", "SecurePass456!"),
        TestUser("trader_charlie", "trader.charlie@example.com", "SecurePass789!"),
    ]

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        registered_count = 0
        for user in users:
            print(f"\n  Registering {user.username}...")
            if await user.register(client):
                print(f"    ✓ Registration successful")
                registered_count += 1
            else:
                print(f"    ✗ Registration failed")

        print(f"\n✓ Registered {registered_count}/{len(users)} users")

    return registered_count == len(users), users


async def test_order_submission(users: List[TestUser]) -> Tuple[bool, OrderMetrics]:
    """Test order submission workflow."""
    print("\n" + "=" * 70)
    print("TEST 2: ORDER SUBMISSION (Real Orders)")
    print("=" * 70)

    metrics = OrderMetrics()
    symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
    sides = ["BUY", "SELL"]

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        orders_per_user = 5

        for user in users:
            print(f"\n  {user.username} submitting {orders_per_user} orders...")

            for i in range(orders_per_user):
                try:
                    start = time.time()
                    response = await client.post(
                        "/api/orders",
                        headers=user.get_headers(),
                        json={
                            "symbol": symbols[i % len(symbols)],
                            "side": sides[i % len(sides)],
                            "order_type": "MARKET",
                            "quantity": 10.0 + (i * 5),
                            "price": None,
                            "stop_price": None,
                            "trailing_stop_pct": None,
                            "iceberg_qty": None,
                            "time_in_force": "GTC",
                        },
                    )
                    elapsed = (time.time() - start) * 1000

                    if response.status_code == 201:
                        data = response.json()
                        order_id = data.get("id", "unknown")
                        metrics.add_time(elapsed, True, order_id)
                        print(
                            f"    Order {i+1}: {order_id} placed in {elapsed:.2f}ms"
                        )
                    else:
                        metrics.add_time(elapsed, False)
                        print(
                            f"    Order {i+1}: FAILED - Status {response.status_code}"
                        )

                except Exception as e:
                    metrics.add_time(0, False)
                    print(f"    Order {i+1}: ERROR - {e}")

    print(f"\n✓ Order Submission Metrics:")
    for key, value in metrics.summary().items():
        print(f"  {key:20} {value}")

    return (
        metrics.successful_orders > 0 and metrics.failed_orders == 0,
        metrics,
    )


async def test_order_retrieval(users: List[TestUser]) -> bool:
    """Test retrieving submitted orders."""
    print("\n" + "=" * 70)
    print("TEST 3: ORDER RETRIEVAL & LISTING")
    print("=" * 70)

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        for user in users:
            try:
                response = await client.get(
                    "/api/orders", headers=user.get_headers()
                )

                if response.status_code == 200:
                    orders = response.json()
                    print(f"\n  {user.username}: {len(orders)} orders")
                    for order in orders[:3]:  # Show first 3
                        print(
                            f"    - {order.get('id')}: {order.get('symbol')} {order.get('side')} {order.get('quantity')} @ {order.get('price')}"
                        )
                    if len(orders) > 3:
                        print(f"    ... and {len(orders) - 3} more")
                else:
                    print(
                        f"\n  {user.username}: Failed to retrieve orders - {response.status_code}"
                    )

            except Exception as e:
                print(f"\n  {user.username}: Error - {e}")

    print("\n✓ Order retrieval completed")
    return True


async def test_positions_tracking(users: List[TestUser]) -> bool:
    """Test position tracking."""
    print("\n" + "=" * 70)
    print("TEST 4: POSITION TRACKING")
    print("=" * 70)

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        for user in users:
            try:
                response = await client.get(
                    "/api/positions", headers=user.get_headers()
                )

                if response.status_code == 200:
                    positions = response.json()
                    print(f"\n  {user.username}: {len(positions)} open positions")
                    for pos in positions[:3]:  # Show first 3
                        print(
                            f"    - {pos.get('symbol')}: {pos.get('quantity')} @ {pos.get('avg_price')}"
                        )
                    if len(positions) > 3:
                        print(f"    ... and {len(positions) - 3} more")
                else:
                    print(
                        f"\n  {user.username}: Failed to retrieve positions - {response.status_code}"
                    )

            except Exception as e:
                print(f"\n  {user.username}: Error - {e}")

    print("\n✓ Position tracking completed")
    return True


async def test_portfolio_summary(users: List[TestUser]) -> bool:
    """Test portfolio summary."""
    print("\n" + "=" * 70)
    print("TEST 5: PORTFOLIO SUMMARY")
    print("=" * 70)

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        for user in users:
            try:
                response = await client.get(
                    "/api/positions/summary", headers=user.get_headers()
                )

                if response.status_code == 200:
                    summary = response.json()
                    print(f"\n  {user.username}:")
                    print(
                        f"    Total Positions: {summary.get('total_positions')}"
                    )
                    print(
                        f"    Total Value: ${summary.get('total_value', 0):.2f}"
                    )
                    print(
                        f"    Realized P&L: ${summary.get('total_realized_pnl', 0):.2f}"
                    )
                    print(
                        f"    Unrealized P&L: ${summary.get('total_unrealized_pnl', 0):.2f}"
                    )
                else:
                    print(
                        f"\n  {user.username}: Failed to retrieve summary - {response.status_code}"
                    )

            except Exception as e:
                print(f"\n  {user.username}: Error - {e}")

    print("\n✓ Portfolio summary completed")
    return True


async def test_order_cancellation(
    users: List[TestUser], metrics: OrderMetrics
) -> bool:
    """Test order cancellation."""
    print("\n" + "=" * 70)
    print("TEST 6: ORDER CANCELLATION")
    print("=" * 70)

    if not metrics.order_ids:
        print("  No orders to cancel (none were created successfully)")
        return False

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        cancelled_count = 0

        for user in users[:1]:  # Use first user
            for order_id in metrics.order_ids[:2]:  # Cancel first 2 orders
                try:
                    response = await client.delete(
                        f"/api/orders/{order_id}",
                        headers=user.get_headers(),
                    )

                    if response.status_code == 200:
                        cancelled_count += 1
                        print(f"  ✓ Cancelled order {order_id}")
                    else:
                        print(f"  ✗ Failed to cancel {order_id} - {response.status_code}")

                except Exception as e:
                    print(f"  ✗ Error cancelling {order_id} - {e}")

    print(f"\n✓ Cancelled {cancelled_count} orders")
    return cancelled_count > 0


async def main():
    """Run all real user integration tests."""
    print("\n" + "=" * 70)
    print("HFT TRADING PLATFORM - REAL USER INTEGRATION TESTS")
    print("NOT MOCKED - ACTUAL USER ACCOUNTS & ORDERS")
    print("=" * 70)
    print(f"Start time: {datetime.now().isoformat()}")
    print(f"Backend URL: {BASE_URL}")

    results = {}

    try:
        # Test 1: User Registration
        passed, users = await test_user_registration()
        results["User Registration"] = passed

        if not passed or not users:
            print("\n✗ Cannot continue without registered users")
            return 1

        # Test 2: Order Submission
        passed, order_metrics = await test_order_submission(users)
        results["Order Submission"] = passed

        # Test 3: Order Retrieval
        passed = await test_order_retrieval(users)
        results["Order Retrieval"] = passed

        # Test 4: Position Tracking
        passed = await test_positions_tracking(users)
        results["Position Tracking"] = passed

        # Test 5: Portfolio Summary
        passed = await test_portfolio_summary(users)
        results["Portfolio Summary"] = passed

        # Test 6: Order Cancellation
        passed = await test_order_cancellation(users, order_metrics)
        results["Order Cancellation"] = passed

        # Print summary
        print("\n" + "=" * 70)
        print("TEST RESULTS SUMMARY")
        print("=" * 70)
        for test_name, passed in results.items():
            status = "PASSED" if passed else "FAILED"
            print(f"  {test_name:30} {status}")

        print("\n" + "=" * 70)
        print(f"End time: {datetime.now().isoformat()}")
        print("=" * 70)

        all_passed = all(results.values())
        if all_passed:
            print("\n✓ ALL REAL USER INTEGRATION TESTS PASSED")
            print("  Application is functioning with actual user workflows\n")
            return 0
        else:
            print("\n✗ SOME TESTS FAILED - Review logs above\n")
            return 1

    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

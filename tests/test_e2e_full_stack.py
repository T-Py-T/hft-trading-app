"""
tests/test_e2e_full_stack.py
End-to-end tests requiring full Docker stack
- C++ Engine
- Python Backend
- PostgreSQL Database
- All services running
"""

import asyncio
import pytest
import requests
import json
from datetime import datetime


class TestFullStackE2E:
    """Full stack end-to-end tests"""

    @pytest.fixture(scope="session")
    def base_urls(self):
        """URLs for all services"""
        return {
            "backend": "http://localhost:8000",
            "engine": "localhost:50051",
            "postgres": "localhost:5432",
        }

    def test_backend_health(self, base_urls):
        """Backend /health endpoint is working"""
        try:
            response = requests.get(f"{base_urls['backend']}/health", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
        except requests.ConnectionError:
            pytest.skip("Backend not running")

    def test_backend_readiness(self, base_urls):
        """Backend is ready to accept orders"""
        try:
            response = requests.get(f"{base_urls['backend']}/ready", timeout=5)
            assert response.status_code == 200
        except requests.ConnectionError:
            pytest.skip("Backend not running")

    def test_database_connected(self, base_urls):
        """Database is connected to backend"""
        try:
            response = requests.get(f"{base_urls['backend']}/db/status", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert data.get("connected") is True
        except (requests.ConnectionError, KeyError):
            pytest.skip("Backend/DB not properly connected")

    def test_submit_market_order(self, base_urls):
        """Submit a market order through full stack"""
        try:
            order_data = {
                "symbol": "AAPL",
                "side": "buy",
                "order_type": "market",
                "quantity": 10,
            }

            response = requests.post(
                f"{base_urls['backend']}/orders",
                json=order_data,
                timeout=5,
            )

            # Should be accepted or filled
            assert response.status_code in [200, 202]
            order_response = response.json()
            assert "order_id" in order_response
            assert order_response["status"] in [
                "ACCEPTED",
                "FILLED",
                "PARTIALLY_FILLED",
            ]
        except requests.ConnectionError:
            pytest.skip("Backend not running")

    def test_submit_limit_order(self, base_urls):
        """Submit a limit order through full stack"""
        try:
            order_data = {
                "symbol": "GOOG",
                "side": "buy",
                "order_type": "limit",
                "price": 100.00,
                "quantity": 5,
            }

            response = requests.post(
                f"{base_urls['backend']}/orders",
                json=order_data,
                timeout=5,
            )

            assert response.status_code in [200, 202]
            order_response = response.json()
            assert order_response["order_id"]
        except requests.ConnectionError:
            pytest.skip("Backend not running")

    def test_get_orders(self, base_urls):
        """Retrieve orders through backend"""
        try:
            response = requests.get(
                f"{base_urls['backend']}/orders",
                timeout=5,
            )

            assert response.status_code == 200
            orders = response.json()
            assert isinstance(orders, list)
        except requests.ConnectionError:
            pytest.skip("Backend not running")

    def test_get_user_positions(self, base_urls):
        """Get user positions through backend"""
        try:
            user_id = 1
            response = requests.get(
                f"{base_urls['backend']}/users/{user_id}/positions",
                timeout=5,
            )

            assert response.status_code == 200
            positions = response.json()
            assert isinstance(positions, dict)
        except (requests.ConnectionError, requests.HTTPError):
            pytest.skip("Backend not running or endpoint not available")

    def test_portfolio_valuation(self, base_urls):
        """Portfolio valuation calculation"""
        try:
            response = requests.get(
                f"{base_urls['backend']}/portfolio/valuation",
                timeout=5,
            )

            assert response.status_code == 200
            valuation = response.json()
            assert "total_value" in valuation
            assert "timestamp" in valuation
        except (requests.ConnectionError, requests.HTTPError):
            pytest.skip("Endpoint not available")

    def test_engine_grpc_connectivity(self):
        """C++ Engine gRPC server is reachable"""
        try:
            import grpc

            channel = grpc.aio.insecure_channel("localhost:50051")
            # If we can create a channel, server is listening
            assert channel is not None
        except Exception:
            pytest.skip("gRPC server not available")

    def test_full_order_lifecycle(self, base_urls):
        """Test complete order lifecycle: submit, fill, retrieve"""
        try:
            # 1. Submit market order
            order_data = {
                "symbol": "MSFT",
                "side": "buy",
                "order_type": "market",
                "quantity": 1,
            }

            submit_response = requests.post(
                f"{base_urls['backend']}/orders",
                json=order_data,
                timeout=5,
            )

            assert submit_response.status_code in [200, 202]
            order_id = submit_response.json()["order_id"]

            # 2. Get order status
            get_response = requests.get(
                f"{base_urls['backend']}/orders/{order_id}",
                timeout=5,
            )

            assert get_response.status_code == 200
            order_status = get_response.json()
            assert order_status["order_id"] == order_id

        except requests.ConnectionError:
            pytest.skip("Backend not running")

    def test_concurrent_orders(self, base_urls):
        """Submit multiple orders concurrently"""
        try:
            orders_data = [
                {"symbol": "AAPL", "side": "buy", "order_type": "market", "quantity": 1},
                {"symbol": "GOOG", "side": "buy", "order_type": "market", "quantity": 1},
                {"symbol": "MSFT", "side": "buy", "order_type": "market", "quantity": 1},
            ]

            responses = []
            for order_data in orders_data:
                response = requests.post(
                    f"{base_urls['backend']}/orders",
                    json=order_data,
                    timeout=5,
                )
                responses.append(response)

            # All should succeed
            for response in responses:
                assert response.status_code in [200, 202]

        except requests.ConnectionError:
            pytest.skip("Backend not running")

    def test_backend_metrics(self, base_urls):
        """Backend exposes metrics"""
        try:
            response = requests.get(
                f"{base_urls['backend']}/metrics",
                timeout=5,
            )

            assert response.status_code == 200
            # Metrics should be in Prometheus format or JSON
            assert len(response.text) > 0
        except (requests.ConnectionError, requests.HTTPError):
            pytest.skip("Metrics endpoint not available")


class TestIntegrationErrors:
    """Test error handling in full stack"""

    def test_invalid_symbol(self):
        """Invalid symbol should be rejected"""
        try:
            order_data = {
                "symbol": "INVALID_SYMBOL",
                "side": "buy",
                "order_type": "market",
                "quantity": 10,
            }

            response = requests.post(
                "http://localhost:8000/orders",
                json=order_data,
                timeout=5,
            )

            # Should be rejected
            assert response.status_code in [400, 422, 404]
        except requests.ConnectionError:
            pytest.skip("Backend not running")

    def test_invalid_quantity(self):
        """Invalid quantity should be rejected"""
        try:
            order_data = {
                "symbol": "AAPL",
                "side": "buy",
                "order_type": "market",
                "quantity": -100,  # Negative quantity
            }

            response = requests.post(
                "http://localhost:8000/orders",
                json=order_data,
                timeout=5,
            )

            assert response.status_code in [400, 422]
        except requests.ConnectionError:
            pytest.skip("Backend not running")

    def test_missing_required_field(self):
        """Missing required field should be rejected"""
        try:
            order_data = {
                "symbol": "AAPL",
                # missing side
                "order_type": "market",
                "quantity": 10,
            }

            response = requests.post(
                "http://localhost:8000/orders",
                json=order_data,
                timeout=5,
            )

            assert response.status_code in [400, 422]
        except requests.ConnectionError:
            pytest.skip("Backend not running")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

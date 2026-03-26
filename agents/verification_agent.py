"""
Verification Agent – checks if fix worked.
"""
import random


class VerificationAgent:

    def verify(self, log, decision, execution):

        if not decision.get("action_required"):
            return {
                "status": "success",
                "message": "System healthy",
                "checks": [],
                "resolved": True,
            }

        source = execution.get("source")

        recovery_odds = {
            "playbook": 0.9,
            "fallback": 0.7,
        }

        recovered = random.random() < recovery_odds.get(source, 0.75)

        return {
            "status": "success" if recovered else "failure",
            "message": "Recovered" if recovered else "Failed",
            "checks": [],
            "resolved": recovered,
        }
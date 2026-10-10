"""
Automated unit verification for DOOM AI application scanner, controllers, task planner, and intent routing.
"""

import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.ai.task_planner import task_planner
from backend.ai.intent_parser import IntentParser
from backend.automation.registry import app_registry
from backend.automation.controllers.calculator_controller import CalculatorController
from backend.execution.application_scanner import application_scanner


def test_task_planner():
    print("--- 1. Testing Task Planner Decomposition ---")

    # Test 1: WhatsApp (various natural wordings)
    for q in [
        "Hey Doom, open WhatsApp and send a message to Amma saying hi",
        "open WhatsApp and send message to Amma saying hi",
        "open WhatsApp and send message to Amma hi",
        "open WhatsApp send message to Amma hi",
        "open WhatsApp and send hi to Amma",
        "open WhatsApp and message Amma saying hi",
        "send a message to Amma saying hi",
        "message Amma saying hi",
        "message Amma hi"
    ]:
        p = task_planner.plan(q)
        assert p is not None, f"Failed to plan WhatsApp query: '{q}'"
        assert p.target_app == "whatsapp", f"Expected whatsapp for '{q}', got {p.target_app}"
        assert p.steps[1].params["contact"].lower() == "amma"
        assert p.steps[1].params["message"].lower() == "hi"
    print(f"✓ All natural WhatsApp command variations successfully decomposed!")

    # Test 2: Calculator
    query2 = "open calculator and calculate 250 multiplied by 45"
    plan2 = task_planner.plan(query2)
    assert plan2 is not None, "Failed to plan Calculator query"
    assert plan2.target_app == "calculator"
    assert "multiplied by" in plan2.steps[1].params["expression"]
    print(f"✓ Calculator plan: {len(plan2.steps)} steps generated for '{plan2.steps[1].params['expression']}'")

    # Test 3: Chrome Search & Open Top Result
    query3 = "open chrome, search for java inheritance and open the first result"
    plan3 = task_planner.plan(query3)
    assert plan3 is not None, "Failed to plan Chrome query"
    assert plan3.target_app == "chrome"
    assert plan3.steps[1].action == "search_and_open_top_result"
    assert plan3.steps[1].params["query"] == "java inheritance"
    print(f"✓ Chrome search plan: '{plan3.steps[1].params['query']}'")

    # Test 4: Spotify Playback
    query4 = "open spotify and play bohemian rhapsody"
    plan4 = task_planner.plan(query4)
    assert plan4 is not None, "Failed to plan Spotify query"
    assert plan4.target_app == "spotify"
    assert plan4.steps[1].params["query"] == "bohemian rhapsody"
    print(f"✓ Spotify plan: search_and_play '{plan4.steps[1].params['query']}'")

    # Test 5: File Explorer
    query5 = "open downloads folder"
    plan5 = task_planner.plan(query5)
    assert plan5 is not None, "Failed to plan File Explorer query"
    assert plan5.target_app == "explorer"
    assert plan5.steps[0].params["folder"] == "downloads"
    print(f"✓ Explorer plan: open folder '{plan5.steps[0].params['folder']}'")

    # Test 6: VS Code Run
    query6 = "open vs code and run the project"
    plan6 = task_planner.plan(query6)
    assert plan6 is not None, "Failed to plan VS Code query"
    assert plan6.target_app == "vscode"
    print(f"✓ VS Code plan: action '{plan6.steps[1].action}'")


def test_intent_parser():
    print("\n--- 2. Testing IntentParser Integration ---")
    res1 = IntentParser.parse("open WhatsApp and send a message to Amma saying hi")
    assert res1["intent"] == "EXECUTE_TASK_PLAN", f"Expected EXECUTE_TASK_PLAN, got {res1['intent']}"
    assert res1["params"]["plan"].target_app == "whatsapp"
    print("✓ IntentParser successfully routed compound WhatsApp query to EXECUTE_TASK_PLAN")

    res2 = IntentParser.parse("open calculator and calculate 250 multiplied by 45")
    assert res2["intent"] == "EXECUTE_TASK_PLAN"
    print("✓ IntentParser successfully routed Calculator query to EXECUTE_TASK_PLAN")

    res3 = IntentParser.parse("close file explorer")
    assert res3["intent"] == "CLOSE_APPLICATION"
    assert res3["params"]["app_name"] == "file explorer"
    print("✓ IntentParser properly retained single-action CLOSE_APPLICATION for 'close file explorer'")

    res4 = IntentParser.parse("close setting")
    assert res4["intent"] == "CLOSE_APPLICATION"
    assert res4["params"]["app_name"] == "setting"
    print("✓ IntentParser correctly routed 'close setting' to CLOSE_APPLICATION")

    res5 = IntentParser.parse("close settings")
    assert res5["intent"] == "CLOSE_APPLICATION"
    assert res5["params"]["app_name"] == "settings"
    print("✓ IntentParser correctly routed 'close settings' to CLOSE_APPLICATION")


def test_calculator_logic():
    print("\n--- 3. Testing Calculator Math Evaluation ---")
    calc = CalculatorController()
    cleaned, val = calc._normalize_math_expression("250 multiplied by 45")
    assert val == 11250, f"Expected 11250, got {val}"
    formatted = f"{val:,}"
    assert formatted == "11,250", f"Expected '11,250', got {formatted}"
    print(f"✓ 250 multiplied by 45 evaluated to: {formatted}")

    cleaned2, val2 = calc._normalize_math_expression("1000 divided by 8")
    assert val2 == 125
    print(f"✓ 1000 divided by 8 evaluated to: {val2}")


def test_app_registry():
    print("\n--- 4. Testing App Registry Resolution ---")
    wa = app_registry.get_controller("whatsapp")
    assert wa.name == "WhatsApp"

    calc = app_registry.get_controller("calculator")
    assert calc.name == "Calculator"

    chrome = app_registry.get_controller("chrome")
    assert chrome.name == "Browser"

    spotify = app_registry.get_controller("spotify")
    assert spotify.name == "Spotify"

    vscode = app_registry.get_controller("vscode")
    assert vscode.name == "VS Code"

    explorer = app_registry.get_controller("file explorer")
    assert explorer.name == "File Explorer"

    print("✓ All specialized controllers registered and correctly resolved.")


if __name__ == "__main__":
    test_task_planner()
    test_intent_parser()
    test_calculator_logic()
    test_app_registry()
    print("\nALL AUTOMATION TESTS PASSED SUCCESSFULLY! 🚀")

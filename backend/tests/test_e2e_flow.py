"""
End-to-end test: Phase 0 → Phase 1 → Phase 2.

Tests the full user journey:
  1. Health check (P0)
  2. Create user + start interview modules (P1)
  3. Complete all 4 mandatory modules with answers (P1)
  4. Check twin eligibility (P1)
  5. Generate digital twin (P2)
  6. Chat with twin (P2)
  7. Get chat history (P2)

Run with: python tests/test_e2e_flow.py
"""

import asyncio
import json
import sys
import time
from uuid import UUID, uuid4

import httpx

BASE = "http://localhost:8000"
API = f"{BASE}/api/v1"

# Track timing
start_time = time.time()


def elapsed():
    return f"[{time.time() - start_time:.1f}s]"


def fail(msg):
    print(f"\n  FAIL: {msg}")
    sys.exit(1)


def ok(msg=""):
    print(f"  OK {msg}")


async def retry_post(client, url, json_data, max_retries=3, delay=5):
    """Retry a POST request on 500 errors (LLM transient failures)."""
    for attempt in range(max_retries):
        r = await client.post(url, json=json_data)
        if r.status_code != 500:
            return r
        if attempt < max_retries - 1:
            print(f"    Retry {attempt+1}/{max_retries} after 500 error...")
            await asyncio.sleep(delay)
    return r


async def main():
    async with httpx.AsyncClient(timeout=300.0) as client:
        # ==============================================================
        # PHASE 0: Foundation
        # ==============================================================
        print(f"\n{'='*60}")
        print("PHASE 0: Foundation")
        print(f"{'='*60}")

        # 1. Health check
        print(f"\n{elapsed()} Testing health check...")
        r = await client.get(f"{BASE}/health")
        if r.status_code != 200:
            fail(f"Health check failed: {r.status_code}")
        data = r.json()
        assert data["status"] == "healthy", f"Status: {data['status']}"
        assert data["database"] == "connected", f"DB: {data['database']}"
        ok(f"status={data['status']}, db={data['database']}, version={data['version']}")

        # 2. Root endpoint
        print(f"\n{elapsed()} Testing root endpoint...")
        r = await client.get(f"{BASE}/")
        assert r.status_code == 200
        data = r.json()
        ok(f"name={data['name']}, env={data['environment']}")

        # 3. API docs accessible
        print(f"\n{elapsed()} Testing API docs...")
        r = await client.get(f"{BASE}/docs")
        assert r.status_code == 200
        ok("Swagger UI accessible")

        # ==============================================================
        # PHASE 1: Text Interview + Modules
        # ==============================================================
        print(f"\n{'='*60}")
        print("PHASE 1: Text Interview + Modules")
        print(f"{'='*60}")

        # Generate a user ID upfront — the backend will auto-create the user
        user_id = str(uuid4())
        completed_modules = []

        # Module-specific answers targeting each module's signal list
        module_answers = {
            # M1 signals: occupation_lifestyle_overview, age_band, living_context,
            #             self_described_personality, life_stage, daily_routine_pattern
            "M1": [
                "I'm a 28-year-old software engineer living in Mumbai. I work at a tech startup and my typical week involves coding, team meetings, and client calls. I wake up at 8am, exercise for 30 minutes, start work by 10, and usually wrap up by 7pm. Evenings I cook dinner and read or watch something.",
                "I'd describe myself as analytical, curious, and slightly introverted. I'm the kind of person who researches everything before committing. People say I'm reliable and thoughtful, but I can overthink things. I have a dry sense of humor.",
                "I live alone in a 1BHK apartment in Andheri, Mumbai. I moved out of my parents' house about 3 years ago when I started my current job. I'm at an early career stage, focused on learning and building up my savings.",
                "The most important thing in my life right now is growing my career. I want to move into a senior engineering role within the next year. I'm also building a side project on weekends — a small SaaS tool.",
                "My close friends would call me dependable, nerdy, and thoughtful. They say I always come through when it matters but I tend to overthink simple decisions.",
                "My daily routine is very structured. Wake up at 8, gym until 9, work 10 to 7, cook dinner, read or code on my side project until 11. Weekends are more flexible — I meet friends, explore cafes, or just stay in.",
            ],
            # M2 signals: speed_vs_deliberation, gut_vs_data, risk_appetite,
            #             reversibility_sensitivity, information_needs, decision_regret_pattern
            "M2": [
                "For my last big purchase, a laptop, I spent about two weeks researching. I compared specs across 5-6 models, watched review videos, read Reddit threads, and made a spreadsheet. I need to feel confident I'm making the right choice before I spend that kind of money.",
                "I'm definitely more of a data-driven decision maker. I rarely go with my gut for anything important. I need to see comparisons, reviews, and ideally talk to someone who already owns the thing. For small decisions like what to eat, I go with my gut.",
                "I'm fairly risk-averse with money — I wouldn't invest in crypto or gamble. But I'm willing to take career risks for the right opportunity. I left a stable corporate job to join a startup because I believed in the product.",
                "I'm very sensitive to whether a decision is reversible. If I can return something or cancel a subscription, I decide much faster. But for irreversible things like signing a lease or taking a new job, I deliberate for days or weeks.",
                "I once impulsively bought a gym membership at a fancy gym. A month later I realized I barely used the extra facilities and regretted not going with the cheaper option. Since then I always do a trial period before committing.",
                "When I look back at past decisions, I mostly regret the ones I rushed into. So now I have a personal rule: for anything over 5000 rupees, I sleep on it for at least one night before buying.",
            ],
            # M3 signals: control_vs_convenience, price_vs_quality, privacy_vs_personalization,
            #             novelty_vs_familiarity, speed_vs_thoroughness, independence_vs_support
            "M3": [
                "Quality matters more to me than price. I'd rather save up and buy something that lasts 5 years than get the cheap version that breaks in 6 months. For headphones, chairs, and kitchen tools, I always go premium.",
                "I like apps that give me control. I don't want an algorithm deciding everything for me. I prefer to customize my settings, choose my own playlists, and set my own filters. Automatic recommendations are fine as secondary options but I want to be in the driver's seat.",
                "I'm fairly privacy-conscious. I don't like companies tracking my every move, but I accept some personalization if it genuinely improves my experience. I use ad blockers and limit app permissions, but I'll share data with apps I trust if the trade-off is clear.",
                "I tend to stick with brands and products I know work well. I'm not the kind of person who tries every new thing. But once a year or so I'll explore alternatives to make sure I'm not missing out on something better.",
                "I prefer to be thorough rather than fast. Whether it's cooking, coding, or shopping, I'd rather take extra time to do it right than rush and end up with a mediocre result. Speed is only important when there's a real deadline.",
                "I prefer figuring things out on my own. I'll read documentation, watch tutorials, and troubleshoot before asking someone for help. But for major life decisions, I do consult close friends or family for a second opinion.",
            ],
            # M4 signals: directness, conflict_style, introversion_extroversion,
            #             group_size_comfort, trust_formation, feedback_preference
            "M4": [
                "When I disagree with someone, I prefer to be direct about it but in a respectful way. I won't sugarcoat my opinion but I try to be constructive. In serious conflicts, I stay logical rather than emotional and focus on finding a solution.",
                "I definitely need alone time to recharge. After a full day of meetings and socializing, I need at least an hour by myself to decompress. I enjoy being with people but I'm clearly an introvert who gets drained by large gatherings.",
                "I'm slow to trust new people. I need to see how someone behaves across multiple interactions — whether they follow through on promises and stay consistent. But once I trust someone, I'm very loyal and open.",
                "I strongly prefer one-on-one conversations or small groups of 3-4 people. In larger groups I tend to go quiet and just observe. I feel like the most meaningful conversations happen in intimate settings.",
                "When someone gives me critical feedback, my first reaction is to feel a bit defensive internally, but I've trained myself not to show it. I take time to process it privately, then come back with a clear head. I actually value honest feedback — it helps me grow.",
                "I prefer written communication over phone calls. I like having time to think about my response. In person, I'm a good listener — I ask follow-up questions rather than dominating the conversation.",
            ],
        }

        # 4. Complete all 4 modules (M1 → M4)
        for module_id in ["M1", "M2", "M3", "M4"]:
            print(f"\n{elapsed()} Starting module {module_id}...")

            # Start single module
            start_req = {
                "user_id": user_id,
                "module_id": module_id,
                "input_mode": "text",
                "language_preference": "en",
                "consent": {
                    "accepted": True,
                    "consent_version": "1.0",
                },
            }

            r = await client.post(f"{API}/interviews/start-module", json=start_req)
            if r.status_code not in (200, 201):
                fail(f"Start module {module_id} failed: {r.status_code} - {r.text}")

            data = r.json()
            session_id = data["session_id"]

            first_q = data.get("first_question", {})
            question_id = first_q.get("question_id", "q1")
            ok(f"session={session_id[:8]}..., first_q={question_id}")

            answers = module_answers[module_id]

            module_done = False
            for i, answer in enumerate(answers):
                # Submit answer
                answer_req = {
                    "answer_text": answer,
                    "question_id": question_id,
                    "input_mode": "text",
                }
                r = await retry_post(
                    client, f"{API}/interviews/{session_id}/answer", answer_req
                )
                if r.status_code == 400 and "No active module" in r.text:
                    # Module was already completed by the server
                    print(f"    Module {module_id} auto-completed after {i} answers")
                    module_done = True
                    break
                if r.status_code != 200:
                    fail(f"Answer {i+1} failed: {r.status_code} - {r.text}")

                # Get next question
                r = await retry_post(
                    client, f"{API}/interviews/{session_id}/next-question", {}
                )
                if r.status_code == 400 and "No active module" in r.text:
                    print(f"    Module {module_id} auto-completed after {i+1} answers")
                    module_done = True
                    break
                if r.status_code != 200:
                    fail(f"Next question {i+1} failed: {r.status_code} - {r.text}")

                next_data = r.json()
                status = next_data.get("status")
                question_id = next_data.get("question_id", f"q{i+3}")

                if status == "module_complete" or status == "all_modules_complete":
                    print(f"    Module {module_id} completed after {i+1} answers")
                    module_done = True
                    break

            # Complete module and exit
            r = await client.post(f"{API}/interviews/{session_id}/complete-module")
            if r.status_code == 200:
                complete_data = r.json()
                coverage = complete_data.get("coverage_score", 0)
                confidence = complete_data.get("confidence_score", 0)
                mod_status = complete_data.get("status", "unknown")
                ok(
                    f"Module {module_id} {mod_status}: "
                    f"coverage={coverage:.2f}, confidence={confidence:.2f}, "
                    f"can_generate_twin={complete_data.get('can_generate_twin')}"
                )
                if mod_status == "module_paused":
                    print(f"    WARN: Module {module_id} paused (coverage too low), may affect twin eligibility")
            elif module_done:
                # Module was already completed server-side
                ok(f"Module {module_id} was already completed by server")
            else:
                fail(f"Complete module {module_id} failed: {r.status_code} - {r.text}")

            completed_modules.append(module_id)

        # 5. Check modules status
        print(f"\n{elapsed()} Checking user modules...")
        r = await client.get(f"{API}/interviews/user/{user_id}/modules")
        if r.status_code != 200:
            fail(f"Get modules failed: {r.status_code} - {r.text}")

        modules_data = r.json()
        ok(
            f"completed={modules_data['completed_count']}/{modules_data['total_required']}, "
            f"can_generate_twin={modules_data['can_generate_twin']}"
        )

        if not modules_data["can_generate_twin"]:
            fail("Cannot generate twin despite completing all modules")

        # 7. Check twin eligibility
        print(f"\n{elapsed()} Checking twin eligibility...")
        r = await client.get(f"{API}/interviews/user/{user_id}/twin-eligibility")
        if r.status_code != 200:
            fail(f"Eligibility check failed: {r.status_code}")

        elig_data = r.json()
        assert elig_data["can_generate_twin"] is True, "Not eligible!"
        ok(
            f"eligible=True, completed={elig_data['completed_modules']}, "
            f"missing={elig_data['missing_modules']}"
        )

        # ==============================================================
        # PHASE 2: Twin Generation + Chat
        # ==============================================================
        print(f"\n{'='*60}")
        print("PHASE 2: Twin Generation + Chat")
        print(f"{'='*60}")

        # 8. Generate twin
        print(f"\n{elapsed()} Generating digital twin (this may take 15-30s)...")
        gen_start = time.time()

        gen_req = {
            "trigger": "mandatory_modules_complete",
            "modules_to_include": ["M1", "M2", "M3", "M4"],
        }
        r = await client.post(
            f"{API}/twins/generate?user_id={user_id}", json=gen_req
        )
        gen_time = time.time() - gen_start

        if r.status_code not in (200, 201):
            fail(f"Twin generation failed: {r.status_code} - {r.text}")

        twin_data = r.json()
        twin_id = twin_data["id"]
        ok(
            f"Twin created in {gen_time:.1f}s: "
            f"id={twin_id[:8]}..., "
            f"version={twin_data['version']}, "
            f"status={twin_data['status']}, "
            f"quality={twin_data['quality_label']} ({twin_data['quality_score']:.2f})"
        )

        if twin_data["status"] != "ready":
            fail(f"Twin status is {twin_data['status']}, expected 'ready'")

        # Verify structured profile exists
        if twin_data.get("structured_profile"):
            profile = twin_data["structured_profile"]
            has_keys = [k for k in ["demographics", "personality", "decision_making", "preferences", "communication"] if k in profile]
            ok(f"Structured profile has: {', '.join(has_keys)}")
        else:
            fail("No structured profile in twin response")

        # Verify persona summary exists
        if twin_data.get("persona_summary_text"):
            summary_len = len(twin_data["persona_summary_text"])
            ok(f"Persona summary: {summary_len} chars")
        else:
            fail("No persona summary in twin response")

        # Verify coverage confidence
        if twin_data.get("coverage_confidence"):
            modules_covered = [cc["domain"] for cc in twin_data["coverage_confidence"]]
            ok(f"Coverage for modules: {modules_covered}")
        else:
            print("  WARN: No coverage confidence data")

        # 9. Get twin profile
        print(f"\n{elapsed()} Getting twin profile by ID...")
        r = await client.get(f"{API}/twins/{twin_id}")
        assert r.status_code == 200, f"Get twin failed: {r.status_code}"
        ok(f"Retrieved twin {twin_id[:8]}...")

        # 10. Get user's latest twin
        print(f"\n{elapsed()} Getting user's latest twin...")
        r = await client.get(f"{API}/twins/user/{user_id}")
        assert r.status_code == 200, f"Get user twin failed: {r.status_code}"
        user_twin = r.json()
        assert user_twin["id"] == twin_id, "User twin ID mismatch"
        ok(f"Latest twin matches: v{user_twin['version']}")

        # 11. Get version history
        print(f"\n{elapsed()} Getting version history...")
        r = await client.get(f"{API}/twins/{twin_id}/versions")
        assert r.status_code == 200
        versions = r.json()
        ok(f"{len(versions)} version(s)")

        # 12. Chat with twin — first message
        print(f"\n{elapsed()} Chatting with twin (message 1)...")
        chat_start = time.time()
        chat_req = {
            "message": "Would you prefer a subscription-based or one-time purchase for a productivity app?"
        }
        r = await client.post(
            f"{API}/twins/{twin_id}/chat?user_id={user_id}", json=chat_req
        )
        chat_time = time.time() - chat_start

        if r.status_code != 200:
            fail(f"Chat failed: {r.status_code} - {r.text}")

        chat_data = r.json()
        chat_session_id = chat_data["session_id"]
        ok(
            f"Response in {chat_time:.1f}s: "
            f"confidence={chat_data['confidence_label']} ({chat_data['confidence_score']:.2f}), "
            f"evidence={len(chat_data['evidence_used'])} snippets"
        )
        print(f"    Twin says: \"{chat_data['response_text'][:150]}...\"")

        if chat_data.get("suggested_module"):
            print(f"    Suggested module: {chat_data['suggested_module']}")
        if chat_data.get("coverage_gaps"):
            print(f"    Coverage gaps: {chat_data['coverage_gaps']}")

        # 13. Chat — follow-up message (same session)
        print(f"\n{elapsed()} Chatting with twin (message 2, follow-up)...")
        chat_req2 = {
            "message": "What about for a meal delivery service — subscription or pay per order?",
            "session_id": chat_session_id,
        }
        r = await client.post(
            f"{API}/twins/{twin_id}/chat?user_id={user_id}", json=chat_req2
        )
        assert r.status_code == 200, f"Follow-up chat failed: {r.status_code}"
        chat_data2 = r.json()
        assert chat_data2["session_id"] == chat_session_id, "Session changed unexpectedly"
        ok(
            f"confidence={chat_data2['confidence_label']} ({chat_data2['confidence_score']:.2f}), "
            f"evidence={len(chat_data2['evidence_used'])} snippets"
        )
        print(f"    Twin says: \"{chat_data2['response_text'][:150]}...\"")

        # 14. Chat — question about uncovered domain
        print(f"\n{elapsed()} Chatting with twin (message 3, testing coverage gaps)...")
        chat_req3 = {
            "message": "How do you handle your health and fitness routine? What supplements do you take?",
            "session_id": chat_session_id,
        }
        r = await client.post(
            f"{API}/twins/{twin_id}/chat?user_id={user_id}", json=chat_req3
        )
        assert r.status_code == 200
        chat_data3 = r.json()
        ok(
            f"confidence={chat_data3['confidence_label']} ({chat_data3['confidence_score']:.2f})"
        )
        print(f"    Twin says: \"{chat_data3['response_text'][:150]}...\"")
        if chat_data3.get("suggested_module"):
            ok(f"Correctly suggests module: {chat_data3['suggested_module']}")

        # 15. Get chat history
        print(f"\n{elapsed()} Getting chat history...")
        r = await client.get(
            f"{API}/twins/{twin_id}/chat/{chat_session_id}/history"
        )
        assert r.status_code == 200
        history = r.json()
        msg_count = len(history["messages"])
        user_msgs = sum(1 for m in history["messages"] if m["role"] == "user")
        twin_msgs = sum(1 for m in history["messages"] if m["role"] == "twin")
        ok(f"{msg_count} messages (user={user_msgs}, twin={twin_msgs})")

        # 16. List chat sessions
        print(f"\n{elapsed()} Listing chat sessions...")
        r = await client.get(f"{API}/twins/{twin_id}/chat/sessions")
        assert r.status_code == 200
        sessions = r.json()
        ok(f"{len(sessions)} session(s)")

        # ==============================================================
        # SUMMARY
        # ==============================================================
        total_time = time.time() - start_time
        print(f"\n{'='*60}")
        print("E2E TEST SUMMARY")
        print(f"{'='*60}")
        print(f"  Total time: {total_time:.1f}s")
        print(f"  User ID: {user_id}")
        print(f"  Twin ID: {twin_id}")
        print(f"  Twin quality: {twin_data['quality_label']} ({twin_data['quality_score']:.2f})")
        print(f"  Twin generation: {gen_time:.1f}s")
        print(f"  Chat messages: {msg_count}")
        print(f"  Phase 0: PASS (health, root, docs)")
        print(f"  Phase 1: PASS (4 modules completed)")
        print(f"  Phase 2: PASS (twin generated + 3 chat messages)")
        print(f"\n  ALL PHASES PASSED")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())

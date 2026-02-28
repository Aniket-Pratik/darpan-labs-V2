"""Seed script: Create dummy twins for testing the experiment flow.

Run from backend/ directory:
    python scripts/seed_dummy_twins.py
"""

import asyncio
import json
import random
import sys
import uuid
from pathlib import Path

# Add parent dir to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import async_session_factory, engine, init_db
from app.models.user import User
from app.models.twin import TwinProfile, EvidenceSnippet
from app.models.interview import InterviewSession, InterviewModule

# 8 diverse persona profiles for testing
PERSONAS = [
    {
        "name": "Priya Sharma",
        "modules": ["M1", "M2", "M3", "M4"],
        "quality_label": "base",
        "quality_score": 0.72,
        "persona_summary": (
            "I'm Priya, a 28-year-old UX designer living in Bangalore with my partner. "
            "I'm detail-oriented and prefer things to be well-planned. I tend to research "
            "extensively before making purchases — I'll read at least 10 reviews before "
            "buying anything over 2000 rupees. I value quality over brand names and prefer "
            "sustainable products when possible. I'm an introvert who recharges alone but "
            "enjoys deep conversations. I'm health-conscious, do yoga 4 times a week, and "
            "prefer home-cooked meals. I'm cautious with money but willing to splurge on "
            "experiences like travel."
        ),
        "profile": {
            "demographics": {"age_band": "25-30", "occupation_type": "tech/design", "living_context": "urban apartment with partner", "life_stage": "early career"},
            "personality": {"self_description": "Detail-oriented introvert who values depth over breadth"},
            "decision_making": {"speed_vs_deliberation": "highly deliberate", "gut_vs_data": "data-driven", "risk_appetite": "moderate-low"},
        },
        "evidence": [
            {"text": "I always check at least 10 reviews before buying anything significant. I use comparison sites religiously.", "category": "behavior"},
            {"text": "I value sustainability — I'll pay 15-20% more for eco-friendly options.", "category": "preference"},
            {"text": "I'm very introverted. Large gatherings drain me. I prefer one-on-one conversations.", "category": "personality"},
            {"text": "I do yoga 4 times a week and meal-prep on Sundays. Health is a top priority.", "category": "behavior"},
            {"text": "I'm cautious with regular spending but I'll invest in travel experiences without hesitation.", "category": "decision_rule"},
        ],
    },
    {
        "name": "Rahul Verma",
        "modules": ["M1", "M2", "M3", "M4", "A1"],
        "quality_label": "enhanced",
        "quality_score": 0.81,
        "persona_summary": (
            "I'm Rahul, 34, a startup founder in Delhi. I'm fast-paced and make decisions "
            "quickly — I trust my gut more than spreadsheets. I'm brand-loyal once I find "
            "something that works, especially for tech products. I'm extremely social and "
            "energized by networking events. I value status symbols to some degree — I think "
            "how you present yourself matters in business. I'm a night owl who works best "
            "after 10 PM. I eat out most days and my fitness routine is inconsistent. Money "
            "is a tool for growth, not security."
        ),
        "profile": {
            "demographics": {"age_band": "30-35", "occupation_type": "entrepreneur", "living_context": "urban apartment solo", "life_stage": "mid career"},
            "personality": {"self_description": "Energetic extrovert, risk-taker, quick decision maker"},
            "decision_making": {"speed_vs_deliberation": "very fast", "gut_vs_data": "gut-driven", "risk_appetite": "high"},
        },
        "evidence": [
            {"text": "I make decisions fast. If I overthink I lose opportunities. I trust my instinct.", "category": "decision_rule"},
            {"text": "Once I find a brand I like, I stick with it. I've used Apple everything for 8 years.", "category": "preference"},
            {"text": "I'm a total extrovert. I get energy from people. I go to 3-4 networking events a month.", "category": "personality"},
            {"text": "I eat out almost every day. I don't have time to cook and I enjoy trying new restaurants.", "category": "behavior"},
            {"text": "I believe in spending money to make money. I'll invest in anything that could 10x.", "category": "decision_rule"},
            {"text": "My morning starts at 9 but I peak after 10 PM. That's when I do my best work.", "category": "context"},
        ],
    },
    {
        "name": "Ananya Reddy",
        "modules": ["M1", "M2", "M3", "M4", "A2"],
        "quality_label": "enhanced",
        "quality_score": 0.78,
        "persona_summary": (
            "I'm Ananya, 26, a marketing analyst in Mumbai. I'm price-conscious but not "
            "cheap — I look for value. I spend a lot of time comparing options online and "
            "rely heavily on Instagram and YouTube reviews. I'm moderately social, prefer "
            "small groups to big parties. I'm quite impulsive with fashion purchases but "
            "very careful with electronics and subscriptions. I budget carefully and track "
            "every expense in an app. I love trying new food and experiences."
        ),
        "profile": {
            "demographics": {"age_band": "25-30", "occupation_type": "corporate/marketing", "living_context": "shared apartment", "life_stage": "early career"},
            "personality": {"self_description": "Analytical but occasionally impulsive, value-seeker"},
            "decision_making": {"speed_vs_deliberation": "mixed — depends on category", "gut_vs_data": "data for big purchases, impulse for small", "risk_appetite": "moderate"},
        },
        "evidence": [
            {"text": "I track every expense in an app. I know exactly where my money goes each month.", "category": "behavior"},
            {"text": "For fashion, I'm impulsive — I'll see something on Instagram and buy it. For electronics, I research for days.", "category": "decision_rule"},
            {"text": "Instagram and YouTube reviews are my primary source for product discovery.", "category": "preference"},
            {"text": "I prefer small groups of 4-5 people. Big parties make me feel lost.", "category": "personality"},
            {"text": "I love food exploration — I try at least 2 new restaurants every month.", "category": "behavior"},
        ],
    },
    {
        "name": "Vikram Patel",
        "modules": ["M1", "M2", "M3", "M4", "A1", "A3"],
        "quality_label": "rich",
        "quality_score": 0.86,
        "persona_summary": (
            "I'm Vikram, 42, a senior engineering manager at a large MNC in Hyderabad. "
            "I'm methodical in my approach to everything — decisions, spending, relationships. "
            "I value stability and long-term thinking. I'm not swayed by trends or marketing. "
            "I research thoroughly, prefer established brands, and almost never make impulse "
            "purchases. I prioritize family time over social life. I exercise daily — running "
            "in the morning is non-negotiable. I'm career-driven but believe in work-life "
            "boundaries. I invest systematically in mutual funds."
        ),
        "profile": {
            "demographics": {"age_band": "40-45", "occupation_type": "tech/management", "living_context": "owned house with family", "life_stage": "established career"},
            "personality": {"self_description": "Methodical, stability-seeking, family-oriented"},
            "decision_making": {"speed_vs_deliberation": "very deliberate", "gut_vs_data": "strongly data-driven", "risk_appetite": "low"},
        },
        "evidence": [
            {"text": "I never buy anything on impulse. I maintain a wishlist and wait at least a week before purchasing.", "category": "decision_rule"},
            {"text": "Established brands give me confidence. I'll pay more for reliability and warranty.", "category": "preference"},
            {"text": "Family dinner at 8 PM is sacred. I leave office by 6:30 no matter what.", "category": "behavior"},
            {"text": "I run 5km every morning at 5:30 AM. It's been my routine for 7 years.", "category": "behavior"},
            {"text": "I invest 30% of my income in SIPs. Long-term wealth building is my strategy.", "category": "decision_rule"},
            {"text": "I'm career-driven but I set hard boundaries. No work emails after 7 PM.", "category": "behavior"},
            {"text": "I want to become a VP in the next 3 years. I'm actively seeking leadership programs.", "category": "context"},
        ],
    },
    {
        "name": "Meera Iyer",
        "modules": ["M1", "M2", "M3", "M4"],
        "quality_label": "base",
        "quality_score": 0.65,
        "persona_summary": (
            "I'm Meera, 22, a final-year engineering student in Chennai. I'm still figuring "
            "out what I want from life. I'm very budget-conscious — student life means every "
            "rupee counts. I rely heavily on peer recommendations and social media for "
            "decisions. I'm adventurous and open to trying new things. I'm quite social "
            "and active on multiple platforms. I don't have strong brand loyalty — I go "
            "wherever the best deal is."
        ),
        "profile": {
            "demographics": {"age_band": "20-25", "occupation_type": "student", "living_context": "hostel", "life_stage": "student"},
            "personality": {"self_description": "Adventurous, social, deal-seeking, still exploring identity"},
            "decision_making": {"speed_vs_deliberation": "moderate speed", "gut_vs_data": "peer-influenced", "risk_appetite": "moderate-high"},
        },
        "evidence": [
            {"text": "I always check for coupon codes and cashback offers before buying anything.", "category": "behavior"},
            {"text": "I don't care about brands much. Whichever gives me the best value wins.", "category": "preference"},
            {"text": "My friends' recommendations matter a lot. If 3 friends say something is good, I'll buy it.", "category": "decision_rule"},
            {"text": "I love trying new things — new food, new apps, new places. I get bored with routine.", "category": "personality"},
        ],
    },
    {
        "name": "Arjun Nair",
        "modules": ["M1", "M2", "M3", "M4", "A2", "A4"],
        "quality_label": "rich",
        "quality_score": 0.84,
        "persona_summary": (
            "I'm Arjun, 31, a freelance software developer based in Kochi. I work remotely "
            "and value flexibility above everything. I'm a minimalist — I own few things but "
            "each is high quality. I'm willing to pay premium for tools that improve my "
            "productivity. I learn best by doing, not reading. I'm an introvert who prefers "
            "async communication over meetings. I'm financially conservative but invest "
            "aggressively in upskilling. I cook simple meals and exercise at home."
        ),
        "profile": {
            "demographics": {"age_band": "30-35", "occupation_type": "freelance/tech", "living_context": "rented apartment solo", "life_stage": "mid career"},
            "personality": {"self_description": "Minimalist introvert, values quality and flexibility"},
            "decision_making": {"speed_vs_deliberation": "deliberate", "gut_vs_data": "data-driven", "risk_appetite": "moderate"},
        },
        "evidence": [
            {"text": "I own very few things but each is carefully chosen for quality. I'd rather have 3 great shirts than 10 average ones.", "category": "preference"},
            {"text": "I'll pay 2x for a tool that saves me 30 minutes a day. Productivity tools are my biggest expense.", "category": "decision_rule"},
            {"text": "I learn by building. I'll start a project to learn a new technology rather than watch tutorials.", "category": "behavior"},
            {"text": "I prefer Slack messages over video calls. Async communication respects my focus time.", "category": "preference"},
            {"text": "I invest 40% of my freelance income into courses and certifications. Upskilling is non-negotiable.", "category": "decision_rule"},
            {"text": "I cook simple, healthy meals. Nothing fancy — dal, rice, sabzi. I spend maybe 30 min on cooking.", "category": "behavior"},
        ],
    },
    {
        "name": "Kavya Menon",
        "modules": ["M1", "M2", "M3", "M4", "A1", "A2", "A3"],
        "quality_label": "rich",
        "quality_score": 0.89,
        "persona_summary": (
            "I'm Kavya, 36, a product manager at a fintech company in Bangalore. I'm very "
            "organized and data-driven in my personal life just as much as at work. I maintain "
            "detailed spreadsheets for everything — groceries, investments, vacation planning. "
            "I'm moderately social and love hosting dinner parties. I'm brand-conscious for "
            "certain categories like skincare and coffee but price-driven for commodities. "
            "I exercise 5 times a week — a mix of strength training and swimming. I'm "
            "ambitious and aiming for a director role within 2 years."
        ),
        "profile": {
            "demographics": {"age_band": "35-40", "occupation_type": "tech/product", "living_context": "owned apartment solo", "life_stage": "established career"},
            "personality": {"self_description": "Organized, ambitious, data-driven, moderately social"},
            "decision_making": {"speed_vs_deliberation": "deliberate", "gut_vs_data": "strongly data-driven", "risk_appetite": "moderate"},
        },
        "evidence": [
            {"text": "I maintain spreadsheets for my monthly spending, investment tracking, and even meal planning.", "category": "behavior"},
            {"text": "For skincare and coffee, I only buy specific brands. For groceries, I go wherever is cheapest.", "category": "decision_rule"},
            {"text": "I love hosting dinner parties — usually once a month for 6-8 friends.", "category": "personality"},
            {"text": "I do strength training 3x/week and swim 2x/week. Rest days are for yoga.", "category": "behavior"},
            {"text": "I'm targeting a director role in 2 years. I've mapped out the skills I need and am working on each.", "category": "context"},
            {"text": "I spend carefully on daily things but invest heavily in health, career development, and travel.", "category": "decision_rule"},
            {"text": "I track my spending monthly. I know my exact spend on eating out, subscriptions, and shopping.", "category": "behavior"},
        ],
    },
    {
        "name": "Rohan Joshi",
        "modules": ["M1", "M2", "M3", "M4", "A1", "A2", "A3", "A4"],
        "quality_label": "full",
        "quality_score": 0.93,
        "persona_summary": (
            "I'm Rohan, 29, a content creator and part-time MBA student in Pune. I'm a "
            "social butterfly who thrives on variety and new experiences. I'm an early "
            "adopter — I want to try the latest products, apps, and restaurants before anyone "
            "else. I'm not particularly price-sensitive for things that excite me, but I "
            "negotiate hard for routine purchases. I'm a morning person who plans my day "
            "the night before. I'm passionate about fitness — gym 6 days a week. I want to "
            "build my own media brand in the next 5 years. I learn best from discussions "
            "and debates."
        ),
        "profile": {
            "demographics": {"age_band": "25-30", "occupation_type": "content creator + student", "living_context": "rented apartment with roommate", "life_stage": "career transition"},
            "personality": {"self_description": "Social, early-adopter, ambitious, experience-driven"},
            "decision_making": {"speed_vs_deliberation": "fast for new things, moderate for big purchases", "gut_vs_data": "gut for experiences, data for investments", "risk_appetite": "high"},
        },
        "evidence": [
            {"text": "I want to be the first to try new things. I signed up for 5 beta programs this year.", "category": "behavior"},
            {"text": "For exciting new products, price is secondary. For household stuff, I'll negotiate for every rupee.", "category": "decision_rule"},
            {"text": "I plan my entire next day the night before. I use time-blocking in Google Calendar.", "category": "behavior"},
            {"text": "Gym 6 days a week. It's my anchor habit — everything else flows from it.", "category": "behavior"},
            {"text": "My 5-year plan is to build a media brand with 1M followers and launch my own product line.", "category": "context"},
            {"text": "I learn best when I can discuss and debate ideas. Solo reading doesn't stick for me.", "category": "preference"},
            {"text": "I thrive on variety. I'd never eat at the same restaurant twice in a month.", "category": "personality"},
            {"text": "I'm very social — I need at least 3 social outings a week or I feel drained.", "category": "personality"},
        ],
    },
]


async def seed():
    await init_db()

    async with async_session_factory() as db:
        created_twins = []

        for persona in PERSONAS:
            # Create user
            user_id = uuid.uuid4()
            user = User(
                id=user_id,
                email=f"seed_{persona['name'].lower().replace(' ', '_')}@darpan.test",
                display_name=persona["name"],
            )
            db.add(user)
            await db.flush()

            # Create twin profile
            twin_id = uuid.uuid4()
            twin = TwinProfile(
                id=twin_id,
                user_id=user_id,
                version=1,
                status="ready",
                modules_included=persona["modules"],
                quality_label=persona["quality_label"],
                quality_score=persona["quality_score"],
                structured_profile_json=persona["profile"],
                persona_summary_text=persona["persona_summary"],
                coverage_confidence={
                    "by_module": {
                        m: {
                            "coverage": round(random.uniform(0.6, 0.95), 2),
                            "confidence": round(random.uniform(0.55, 0.9), 2),
                            "signals_captured": [],
                        }
                        for m in persona["modules"]
                    }
                },
                extraction_meta={"model": "gpt-4-turbo-preview", "source": "seed_script"},
            )
            db.add(twin)
            await db.flush()

            # Create a dummy interview session + modules (needed for evidence FK)
            session_id = uuid.uuid4()
            session = InterviewSession(
                id=session_id,
                user_id=user_id,
                status="completed",
                input_mode="text",
                language_preference="en",
            )
            db.add(session)
            await db.flush()

            # Create a module record for each completed module
            for mod_id in persona["modules"]:
                module = InterviewModule(
                    id=uuid.uuid4(),
                    session_id=session_id,
                    module_id=mod_id,
                    status="completed",
                    question_count=5,
                    coverage_score=round(random.uniform(0.65, 0.90), 2),
                    confidence_score=round(random.uniform(0.60, 0.85), 2),
                )
                db.add(module)
            await db.flush()

            # Create a dummy interview turn for evidence FK
            from app.models.interview import InterviewTurn
            turn_id = uuid.uuid4()
            turn = InterviewTurn(
                id=turn_id,
                session_id=session_id,
                module_id=persona["modules"][0],
                turn_index=1,
                role="user",
                input_mode="text",
                question_text="Tell me about yourself.",
                answer_text="seed data answer",
            )
            db.add(turn)
            await db.flush()

            # Create evidence snippets (no embeddings — experiments use persona + LLM)
            for ev in persona["evidence"]:
                snippet = EvidenceSnippet(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    twin_profile_id=twin_id,
                    module_id=persona["modules"][0],
                    turn_id=turn_id,
                    snippet_text=ev["text"],
                    snippet_category=ev["category"],
                    embedding=None,  # No embeddings for seed data
                    snippet_metadata={"source": "seed_script"},
                )
                db.add(snippet)

            await db.flush()
            created_twins.append((persona["name"], twin_id, persona["quality_label"]))
            print(f"  Created: {persona['name']} ({persona['quality_label']}) — twin_id: {twin_id}")

        await db.commit()

        print(f"\n{'='*60}")
        print(f"Created {len(created_twins)} dummy twins!")
        print(f"{'='*60}")
        print("\nYou can now:")
        print("1. Go to /experiments/new in the frontend")
        print("2. Create a cohort with these twins")
        print("3. Run an experiment against them")
        print(f"\nTo use in frontend, set a user_id in localStorage:")
        print(f"  localStorage.setItem('darpan_user_id', '{created_twins[0][1]}')")
        print(f"\nOr visit the dashboard at /dashboard")


if __name__ == "__main__":
    asyncio.run(seed())

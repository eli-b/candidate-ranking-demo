from datetime import datetime, timedelta
from typing import Optional, Any

from superlinked import framework as sl


class Skill(sl.Schema):
    id: sl.IdField  # pyright: ignore[reportIncompatibleMethodOverride]
    name: sl.String


class OpenPosition(sl.Schema):
    id: sl.IdField  # pyright: ignore[reportIncompatibleMethodOverride]
    title: sl.String
    description: sl.String
    allocated_pay: sl.Integer  # In annual USD
    required_date_of_filling: sl.Timestamp
    skill_weights: sl.FloatList  # All skills weighted, ordered by id
    # No years of experience! It's a substitue for skill proficiency
    # No academic background field, for same reason
    created_at: sl.Timestamp


class Candidate(sl.Schema):
    id: sl.IdField  # pyright: ignore[reportIncompatibleMethodOverride]
    # Contact details and other info
    name: sl.String
    email: sl.String
    phone_number: sl.String
    recommended_by: Optional[sl.String]
    # Relevant details
    desired_pay: sl.Integer  # In annual USD
    self_description: sl.String
    date_of_availability: sl.Integer  # int(datetime.timestamp())
    skills_score: sl.Float
    # No age, gender, or photo fields to avoid bias
    created_at: sl.Timestamp


class SkillScore(sl.Schema):
    id: sl.IdField  # pyright: ignore[reportIncompatibleMethodOverride]
    score: sl.Float


class CandidateEvaluation(sl.EventSchema):
    id: sl.IdField  # pyright: ignore[reportIncompatibleMethodOverride]
    candidate: sl.SchemaReference[Candidate]
    skill_score: sl.SchemaReference[SkillScore]
    skill_id: sl.String
    interviewer_name: sl.String
    created_at: sl.CreatedAtField  # pyright: ignore[reportIncompatibleMethodOverride]


def main():
    skill = Skill()
    open_position = OpenPosition()
    candidate = Candidate()
    skill_score = SkillScore()
    candidate_evaluation = CandidateEvaluation()

    skill_source: sl.InMemorySource = sl.InMemorySource(skill)
    position_source: sl.InMemorySource = sl.InMemorySource(open_position)
    candidate_source: sl.InMemorySource = sl.InMemorySource(candidate)
    skill_score_source: sl.InMemorySource = sl.InMemorySource(skill_score)
    evaluation_source: sl.InMemorySource = sl.InMemorySource(candidate_evaluation)

    # Skill and position data
    now = datetime(2025, 11, 12)
    now_timestamp = int(now.timestamp())
    CONTEXT_DATA = {sl.CONTEXT_COMMON: {sl.CONTEXT_COMMON_NOW: now_timestamp}}
    skill_dicts = [
        dict(id="skill1", name="Team player"),
        dict(id="skill2", name="Frontend technologies"),
        dict(id="skill3", name="Culture fit"),
        dict(id="skill4", name="Leadership"),
    ]
    frontend_position_dict: dict[str, Any] = dict(
        id="position1",
        title="Senior Frontend Developer",
        description="We are looking for a skilled frontend developer to join our team. Must be proficient in JavaScript, React, and CSS.",
        allocated_pay=120_000,
        required_date_of_filling=int((now + timedelta(days=50)).timestamp()),
        skill_weights=[
            0.2,  # Team player
            0.5,  # Frontend technologies
            0.3,  # Culture fit
            0.00001,  # Leadership
        ],
        created_at=int((now - timedelta(days=14)).timestamp()),
    )
    skill_id_to_weight: dict[str, float] = dict(zip([skill_dict["id"] for skill_dict in skill_dicts], frontend_position_dict["skill_weights"]))

    # Candidate spaces, effects and index
    description_space = sl.TextSimilaritySpace(text=candidate.self_description, model="sentence-transformers/all-mpnet-base-v2")
    desired_pay_space = sl.NumberSpace(number=candidate.desired_pay, mode=sl.Mode.MINIMUM, min_value=frontend_position_dict["allocated_pay"], max_value=300_000)
    availability_space = sl.NumberSpace(number=candidate.date_of_availability, mode=sl.Mode.MINIMUM,
                                        min_value=now_timestamp, max_value=frontend_position_dict["required_date_of_filling"])
    skills_score_space = sl.NumberSpace(number=[candidate.skills_score, skill_score.score], mode=sl.Mode.MAXIMUM, min_value=0.0, max_value=10.0)
    evaluation_effects = [
        sl.Effect(
            skills_score_space,
            affected_schema_reference=candidate_evaluation.candidate,  # Its "vector" in the above space is affected
            affecting_schema_reference=weight * candidate_evaluation.skill_score,  # Its "vector" in the above space affects the candidate's "vector"
            filter_=candidate_evaluation.skill_id == skill_id,
        )
        for skill_id, weight in skill_id_to_weight.items()
    ]

    candidate_index = sl.Index(
        spaces=[
            description_space,
            desired_pay_space,
            availability_space,
            skills_score_space
        ],
        effects=evaluation_effects,
        event_influence=1,  # Only evaluations affect the skills score, not the baseline
        temperature=0.5,  # Equal weighting of events
    )

    executor = sl.InMemoryExecutor(
        sources=[skill_source, position_source, candidate_source, skill_score_source, evaluation_source],
        indices=[candidate_index],
        context_data=CONTEXT_DATA
    )
    app = executor.run()

    skill_source.put(skill_dicts)

    position_source.put([
        frontend_position_dict
    ])

    candidate_source.put([
        dict(
            id="candidate1",
            name="Alice Johnson",
            email="Alice@gmail.com",
            phone_number="555-1234",
            desired_pay=115000,
            self_description="Experienced frontend developer with a passion for creating user-friendly web applications.",
            date_of_availability=int((now + timedelta(days=15)).timestamp()),
            skills_score=0,  # Base score before skill evaluations
            created_at=int((now - timedelta(days=7)).timestamp()),
        ),
        dict(
            id="candidate2",
            name="Bob Smith",
            email="Bob@gmail.com",
            phone_number="555-5678",
            desired_pay=125000,
            self_description="Seasoned developer with expertise in React and a strong focus on team collaboration.",
            date_of_availability=int((now + timedelta(days=20)).timestamp()),
            skills_score=0,  # Base score before skill evaluations
            created_at=int((now - timedelta(days=10)).timestamp()),
        ),
    ])
    
    skill_score_source.put([
        dict(id="skillscore1", score=7.0),
        dict(id="skillscore2", score=10.0),
        dict(id="skillscore3", score=7.0),
        dict(id="skillscore4", score=7.0),
        dict(id="skillscore5", score=8.0),
        dict(id="skillscore6", score=10.0),
    ])

    evaluation_source.put([
        dict(
            id="eval1",
            candidate="candidate1",
            skill_id="skill1",  # Team player
            skill_score="skillscore1",
            interviewer_name="Carol",
            created_at=int((now - timedelta(days=2, hours=2, minutes=10)).timestamp()),
        ),
        dict(
            id="eval2",
            candidate="candidate1",
            skill_id="skill2",  # Frontend technologies
            skill_score="skillscore2",
            interviewer_name="Carol",
            created_at=int((now - timedelta(days=2, hours=2, minutes=5)).timestamp()),
        ),
        dict(
            id="eval3",
            candidate="candidate1",
            skill_id="skill3",  # Culture fit
            skill_score="skillscore3",
            interviewer_name="Carol",
            created_at=int((now - timedelta(days=2, hours=2, minutes=0)).timestamp()),
        ),
        dict(
            id="eval4",
            candidate="candidate2",
            skill_id="skill1",  # Team player
            skill_score="skillscore4",
            interviewer_name="Dave",
            created_at=int((now - timedelta(days=6, hours=2, minutes=10)).timestamp()),
        ),
        dict(
            id="eval5",
            candidate="candidate2",
            skill_id="skill2",  # Frontend technologies
            skill_score="skillscore5",
            interviewer_name="Dave",
            created_at=int((now - timedelta(days=6, hours=2, minutes=5)).timestamp()),
        ),
        dict(
            id="eval6",
            candidate="candidate2",
            skill_id="skill3",  # Culture fit
            skill_score="skillscore6",
            interviewer_name="Dave",
            created_at=int((now - timedelta(days=6, hours=2, minutes=0)).timestamp()),
        ),
    ])

    query = (
        sl.Query(
            candidate_index,
            weights={
                description_space: sl.Param("description_similarity_weight", default=0.03),
                skills_score_space: sl.Param("skills_score_weight", default=0.9),
                desired_pay_space: sl.Param("desired_pay_weight", default=0.03),
                availability_space: sl.Param("availability_weight", default=0.04),
            }
        )
        .find(candidate)
        .similar(description_space, frontend_position_dict["description"])
        # skills score, desired pay similarity and availability similarity are implicitly handled by NumberSpace with MINIMUM/MAXIMUM mode
        .select_all()
    )
    result = app.query(query)
    df = sl.PandasConverter.to_pandas(result)
    print(f"Candidate rankings for position {frontend_position_dict['title']}:")
    print(df)


if __name__ == "__main__":
    main()

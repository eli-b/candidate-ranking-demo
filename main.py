from datetime import datetime
from typing import Optional

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
    required_skills: sl.StringList
    required_skill_weights: sl.FloatList
    # No years of experience! It's a substitue for skill proficiency
    # No academic background field, for same reason
    created_at: sl.Timestamp
    updated_at: sl.Timestamp


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
    date_of_availability: sl.Timestamp
    # No age, gender, or photo fields to avoid bias
    created_at: sl.Timestamp
    updated_at: sl.Timestamp


class CandidateEvaluation(sl.Schema):
    id: sl.IdField  # pyright: ignore[reportIncompatibleMethodOverride]
    candidate_id: sl.String  # Candidate being evaluated
    position_id: sl.String  # Position being applied for
    evaluated_skills: sl.StringList
    evaluated_skill_scores: sl.FloatList
    interviewer_name: sl.String
    created_at: sl.Timestamp
    updated_at: sl.Timestamp


def main():
    skill = Skill()
    open_position = OpenPosition()
    candidate = Candidate()
    candidate_evaluation = CandidateEvaluation()
    skill_source: sl.InMemorySource = sl.InMemorySource(skill)
    position_source: sl.InMemorySource = sl.InMemorySource(open_position)
    candidate_source: sl.InMemorySource = sl.InMemorySource(candidate)
    candidate_evaluation_source: sl.InMemorySource = sl.InMemorySource(candidate_evaluation)

    executor = sl.InMemoryExecutor(sources=[skill_source, position_source, candidate_source, candidate_evaluation_source], indices=[])
    app = executor.run()

    skill_source.put([
        dict(id="skill1", name="Team player"),
        dict(id="skill2", name="Frontend technologies"),
        dict(id="skill3", name="Culture fit"),
        dict(id="skill4", name="Leadership"),
    ])

    position_source.put([
        dict(
            id="position1",
            title="Senior Frontend Developer",
            description="We are looking for a skilled frontend developer to join our team. Must be proficient in JavaScript, React, and CSS.",
            allocated_pay=120000,
            required_date_of_filling=datetime(2025, 12, 1),
            required_skills=[
                "skill1",  # Team player
                "skill2",  # Frontend technologies
                "skill3",  # Culture fit
            ],
            required_skill_weights=[
                0.2,  # Team player
                0.5,  # Frontend technologies
                0.3,  # Culture fit
            ],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ])

    candidate_source.put([
        dict(
            id="candidate1",
            name="Alice Johnson",
            email="Alice@gmail.com",
            phone_number="555-1234",
            desired_pay=115000,
            self_description="Experienced frontend developer with a passion for creating user-friendly web applications.",
            date_of_availability=datetime(2025, 11, 15),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        dict(
            id="candidate2",
            name="Bob Smith",
            email="Bob@gmail.com",
            phone_number="555-5678",
            desired_pay=125000,
            self_description="Seasoned developer with expertise in React and a strong focus on team collaboration.",
            date_of_availability=datetime(2025, 12, 5),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ])

    candidate_evaluation_source.put([
        dict(
            id="eval1",
            candidate_id="candidate1",
            position_id="position1",
            evaluated_skills=[
                "skill1",  # Team player
                "skill2",  # Frontend technologies
                "skill3",  # Culture fit
            ],
            evaluated_skill_scores=[
                8,  # Team player
                9,  # Frontend technologies
                7,  # Culture fit
            ],
            interviewer_name="Carol",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        dict(
            id="eval2",
            candidate_id="candidate2",
            position_id="position1",
            evaluated_skills=[
                "skill1",  # Team player
                "skill2",  # Frontend technologies
                "skill3",  # Culture fit
            ],
            evaluated_skill_scores=[
                7,  # Team player
                8,  # Frontend technologies
                9,  # Culture fit
            ],
            interviewer_name="Dave",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ])


if __name__ == "__main__":
    main()

from datetime import datetime
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
    date_of_availability: sl.Integer  # int(datetime.timestamp())
    # No age, gender, or photo fields to avoid bias
    # Evaluation details
    skill_scores: Optional[sl.FloatList]  # Evaluated skill scores, ordered by skill id
    interviewer_name: sl.String
    created_at: sl.Timestamp
    updated_at: sl.Timestamp


def main():
    skill = Skill()
    open_position = OpenPosition()
    candidate = Candidate()

    skill_source: sl.InMemorySource = sl.InMemorySource(skill)
    position_source: sl.InMemorySource = sl.InMemorySource(open_position)
    candidate_source: sl.InMemorySource = sl.InMemorySource(candidate)

    now = int(datetime(2025, 11, 12).timestamp())

    frontend_position_dict: dict[str, Any] = dict(
        id="position1",
        title="Senior Frontend Developer",
        description="We are looking for a skilled frontend developer to join our team. Must be proficient in JavaScript, React, and CSS.",
        allocated_pay=120_000,
        required_date_of_filling=int(datetime(2025, 12, 15).timestamp()),
        skill_weights=[
            0.2,  # Team player
            0.5,  # Frontend technologies
            0.3,  # Culture fit
            0.0,  # Leadership
        ],
        created_at=now,
        updated_at=now,
    )

    # Candidate spaces and index
    description_space = sl.TextSimilaritySpace(text=candidate.self_description, model="sentence-transformers/all-mpnet-base-v2")
    desired_pay_space = sl.NumberSpace(number=candidate.desired_pay, mode=sl.Mode.MINIMUM, min_value=frontend_position_dict["allocated_pay"], max_value=300_000)
    availability_space = sl.NumberSpace(number=candidate.date_of_availability, mode=sl.Mode.MINIMUM,
                                        min_value=now, max_value=frontend_position_dict["required_date_of_filling"])
    skill_scores_space = sl.CustomSpace(vector=candidate.skill_scores, length=4)
    candidate_index = sl.Index(
        spaces=[
            description_space,
            desired_pay_space,
            availability_space,
            skill_scores_space
        ],
    )

    executor = sl.InMemoryExecutor(sources=[skill_source, position_source, candidate_source], indices=[candidate_index])
    app = executor.run()

    skill_source.put([
        dict(id="skill1", name="Team player"),
        dict(id="skill2", name="Frontend technologies"),
        dict(id="skill3", name="Culture fit"),
        dict(id="skill4", name="Leadership"),
    ])

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
            date_of_availability=int(datetime(2025, 11, 15).timestamp()),
            skill_scores=[
                7,  # Team player
                10,  # Frontend technologies
                7,  # Culture fit
                -1,  # Leadership (not evaluated)
            ],
            interviewer_name="Carol",
            created_at=now,
            updated_at=now,
        ),
        dict(
            id="candidate2",
            name="Bob Smith",
            email="Bob@gmail.com",
            phone_number="555-5678",
            desired_pay=125000,
            self_description="Seasoned developer with expertise in React and a strong focus on team collaboration.",
            date_of_availability=int(datetime(2025, 12, 5).timestamp()),
            skill_scores=[
                7,  # Team player
                8,  # Frontend technologies
                10,  # Culture fit
                -1,  # Leadership (not evaluated)
            ],
            interviewer_name="Dave",
            created_at=now,
            updated_at=now,
        ),
    ])

    query = (
        sl.Query(
            candidate_index,
            weights={
                description_space: sl.Param("description_similarity_weight", default=0.03),
                skill_scores_space: sl.Param("skill_scores_weight", default=0.9),
                desired_pay_space: sl.Param("desired_pay_weight", default=0.03),
                availability_space: sl.Param("availability_weight", default=0.04),
            }
        )
        .find(candidate)
        .similar(skill_scores_space, [10.0, 10.0, 10.0, -1.0])  # weight=frontend_position_dict["skill_weights"] can't provide dynamic weights to CustomSpace :(
        .similar(description_space, frontend_position_dict["description"])
        # desired pay similarity and availability similarity are implicitly handled by NumberSpace with MINIMUM mode
        .select_all()
    )
    result = app.query(query)
    df = sl.PandasConverter.to_pandas(result)
    print(df)


if __name__ == "__main__":
    main()

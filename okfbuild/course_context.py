"""Curated author/work/dialect metadata for the pipeline's known courses.

Keyed by course directory name (course_path.name). Deliberately scoped to
the two real pilot courses only -- extending this to other courses, or
building any kind of automated inference, is a separate, future change.

This gives the LLM gap-filler course-level context ("this gap comes from
the course built around Homer's Odyssey") -- it does NOT mean the specific
generated form is attested in that author's actual surviving text. A
course's vocabulary list is a teaching list, not a concordance of the
source text. Word-level attestation checking is out of scope.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CourseContext:
    author: str | None = None
    work: str | None = None
    dialect: str | None = None


COURSE_CONTEXT: dict[str, CourseContext] = {
    "odyssey": CourseContext(author="Homer", work="Odyssey", dialect="Epic/Ionic"),
    "kavafis_ithaki": CourseContext(author="Constantine P. Cavafy", work="Ithaka"),
}

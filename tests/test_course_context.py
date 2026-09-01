from okfbuild.course_context import COURSE_CONTEXT


def test_odyssey_course_context():
    ctx = COURSE_CONTEXT["odyssey"]
    assert ctx.author == "Homer"
    assert ctx.work == "Odyssey"
    assert ctx.dialect == "Epic/Ionic"


def test_kavafis_ithaki_course_context():
    ctx = COURSE_CONTEXT["kavafis_ithaki"]
    assert ctx.author == "Constantine P. Cavafy"
    assert ctx.work == "Ithaka"
    assert ctx.dialect is None


def test_unmapped_course_lookup_returns_none_not_keyerror():
    assert COURSE_CONTEXT.get("unmapped-course") is None

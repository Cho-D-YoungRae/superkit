package {{pkg:domain}}

/**
 * {{Context}} 애그리거트 루트 — 스텁. 프레임워크를 모르는 순수 Kotlin이다(hex.domain-no-framework).
 * 불변식은 `docs/architecture/domain/{{context}}.md`에서 confirmed로 확정한 뒤 여기에서 강제한다.
 */
class {{Context}}(val id: {{Context}}Id, private var status: {{Context}}Status) {

    fun activate() {
        require(status == {{Context}}Status.DRAFT) { "DRAFT 상태에서만 활성화할 수 있다" }
        status = {{Context}}Status.ACTIVE
    }

    fun status(): {{Context}}Status = status
}

@JvmInline
value class {{Context}}Id(val value: Long)

enum class {{Context}}Status { DRAFT, ACTIVE }

/** 예외는 domain에 둔다 — application에는 명명 규칙이 있다(hex.ports-owned-inside). */
class {{Context}}NotFound(id: {{Context}}Id) : RuntimeException("{{context}} 없음: ${id.value}")

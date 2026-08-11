package {{pkg:domain}}

/**
 * 나가는 쪽만 뒤집는다 — 인터페이스는 domain이 소유하고 구현은 infrastructure에 산다.
 * 이 배치를 규약이 아니라 강제로 만드는 것은 이름이 아니라 `ld.infra-isolated`다.
 */
interface {{Context}}Repository {

    fun findById(id: {{Context}}Id): {{Context}}?

    fun save(aggregate: {{Context}})
}

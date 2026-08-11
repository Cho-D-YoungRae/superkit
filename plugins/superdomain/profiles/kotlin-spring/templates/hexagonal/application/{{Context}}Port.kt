package {{pkg:application}}

import {{pkg:domain}}.{{Context}}
import {{pkg:domain}}.{{Context}}Id

/**
 * out 포트 — 안쪽이 소유하고 adapter가 구현한다. 이름은 기술이 아니라 의도로 짓는다
 * (`{{Context}}JpaPort`는 어댑터가 이름으로 새어 나온 것이다). 포트가 늘면 의도 단위로 쪼갠다.
 */
interface {{Context}}Port {

    fun findById(id: {{Context}}Id): {{Context}}?

    fun save(aggregate: {{Context}})
}

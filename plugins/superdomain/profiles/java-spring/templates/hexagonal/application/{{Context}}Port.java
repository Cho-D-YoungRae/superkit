package {{pkg:application}};

import java.util.Optional;

import {{pkg:domain}}.{{Context}};

/**
 * out 포트 — 안쪽이 소유하고 adapter가 구현한다. 이름은 기술이 아니라 의도로 짓는다
 * ({@code {{Context}}JpaPort}는 어댑터가 이름으로 새어 나온 것이다). 포트가 늘면 의도 단위로
 * 쪼갠다. 시그니처에는 도메인 타입만 오간다 — 영속 엔티티가 여기 나타나면 hex.domain-pure를
 * 우회한 누수다.
 */
public interface {{Context}}Port {

    Optional<{{Context}}> findById({{Context}}.Id id);

    void save({{Context}} aggregate);
}

package {{pkg:usecase}};

import java.util.Optional;

import {{pkg:domain}}.{{Context}};

/**
 * 게이트웨이 인터페이스 — usecase가 소유하고 framework가 구현한다.
 * 시그니처에 도메인 타입만 오간다. 영속 엔티티가 여기 나타나면 cl.domain-pure를 우회한 누수다.
 */
public interface {{Context}}Gateway {

    Optional<{{Context}}> findById({{Context}}.Id id);

    void save({{Context}} aggregate);
}

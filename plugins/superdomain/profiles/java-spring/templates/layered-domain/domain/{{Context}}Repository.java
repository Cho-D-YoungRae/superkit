package {{pkg:domain}};

import java.util.Optional;

/**
 * 나가는 쪽만 뒤집는다 — 인터페이스는 domain이 소유하고 구현은 infrastructure에 산다.
 * 이 배치를 규약이 아니라 강제로 만드는 것은 이름이 아니라 {@code ld.infra-isolated}다.
 * 스프링 데이터를 상속하지 않는 이유는 {@code ld.domain-no-framework}다.
 */
public interface {{Context}}Repository {

    Optional<{{Context}}> findById({{Context}}.Id id);

    void save({{Context}} aggregate);
}

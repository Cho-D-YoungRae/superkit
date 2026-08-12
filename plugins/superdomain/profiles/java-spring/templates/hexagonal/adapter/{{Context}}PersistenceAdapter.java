package {{pkg:adapter}};

import java.util.Optional;

import org.springframework.stereotype.Repository;

import {{pkg:application}}.{{Context}}Port;
import {{pkg:domain}}.{{Context}};

/** out 어댑터 — 도메인 모델 ↔ 영속 엔티티 매핑이 이 레이어의 책임이다. */
@Repository
public class {{Context}}PersistenceAdapter implements {{Context}}Port {

    @Override
    public Optional<{{Context}}> findById({{Context}}.Id id) {
        throw new UnsupportedOperationException("영속 조회 후 도메인 모델로 매핑");
    }

    @Override
    public void save({{Context}} aggregate) {
        throw new UnsupportedOperationException("도메인 모델을 엔티티로 매핑 후 저장");
    }
}

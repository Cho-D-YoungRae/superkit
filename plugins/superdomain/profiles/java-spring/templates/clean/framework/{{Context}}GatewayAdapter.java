package {{pkg:framework}};

import java.util.Optional;

import org.springframework.stereotype.Repository;

import {{pkg:domain}}.{{Context}};
import {{pkg:usecase}}.{{Context}}Gateway;

/** 게이트웨이 구현 — 영속 기술은 가장 바깥 원에서 끝난다. 매핑도 여기의 책임이다. */
@Repository
public class {{Context}}GatewayAdapter implements {{Context}}Gateway {

    @Override
    public Optional<{{Context}}> findById({{Context}}.Id id) {
        throw new UnsupportedOperationException("영속 조회 후 도메인 모델로 매핑");
    }

    @Override
    public void save({{Context}} aggregate) {
        throw new UnsupportedOperationException("도메인 모델을 엔티티로 매핑 후 저장");
    }
}

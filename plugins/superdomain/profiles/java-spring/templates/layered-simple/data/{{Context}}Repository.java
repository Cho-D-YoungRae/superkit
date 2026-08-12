package {{pkg:data}};

import org.springframework.data.jpa.repository.JpaRepository;

/** 스프링 데이터 리포지터리. 이름은 자유다 — data 레이어에는 명명 규칙이 없다. */
public interface {{Context}}Repository extends JpaRepository<{{Context}}, Long> {
}

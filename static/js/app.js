/**
 * AI Study Planner - Frontend Application Logic
 */

document.addEventListener("DOMContentLoaded", () => {
  // 1. DOM 요소 참조
  const plannerForm = document.getElementById("plannerForm");
  const formSection = document.getElementById("formSection");
  const loadingSection = document.getElementById("loadingSection");
  const resultSection = document.getElementById("resultSection");
  const loadingMessage = document.getElementById("loadingMessage");
  const errorAlert = document.getElementById("errorAlert");

  const badgeTarget = document.getElementById("badgeTarget");
  const badgeDday = document.getElementById("badgeDday");
  const planContent = document.getElementById("planContent");
  const trackerScore = document.getElementById("trackerScore");
  const trackerFill = document.getElementById("trackerFill");

  const copyBtn = document.getElementById("copyBtn");
  const downloadBtn = document.getElementById("downloadBtn");
  const restartBtn = document.getElementById("restartBtn");

  // 현재 생성된 원본 마크다운 텍스트 저장용 변수
  let currentRawMarkdown = "";
  let loadingInterval = null;

  // 2. 시험일 기본값 설정 (오늘 기준 30일 뒤를 기본값으로 추천)
  const examDateInput = document.getElementById("examDate");
  const defaultTargetDate = new Date();
  defaultTargetDate.setDate(defaultTargetDate.getDate() + 30);
  const yyyy = defaultTargetDate.getFullYear();
  const mm = String(defaultTargetDate.getMonth() + 1).padStart(2, "0");
  const dd = String(defaultTargetDate.getDate()).padStart(2, "0");
  examDateInput.value = `${yyyy}-${mm}-${dd}`;
  examDateInput.min = new Date().toISOString().split("T")[0];

  // 3. 로딩 안내 문구 롤링 애니메이션
  const loadingMessages = [
    "수험생의 가용 시간과 취약 영역을 정밀 분석 중입니다...",
    "Serper 최신 출제 경향 및 핵심 자료를 탐색하고 있습니다...",
    "에빙하우스 망각곡선 기반 과학적 복습 주기를 설계 중입니다...",
    "실전력 극대화를 위한 일일 맞춤형 실천 루틴을 계산하고 있습니다...",
    "10년 차 수험 컨설턴트의 1:1 맞춤형 최종 플랜을 정리 중입니다..."
  ];

  function startLoadingAnimation() {
    let msgIndex = 0;
    loadingMessage.textContent = loadingMessages[0];
    loadingInterval = setInterval(() => {
      msgIndex = (msgIndex + 1) % loadingMessages.length;
      loadingMessage.textContent = loadingMessages[msgIndex];
    }, 2800);
  }

  function stopLoadingAnimation() {
    if (loadingInterval) {
      clearInterval(loadingInterval);
      loadingInterval = null;
    }
  }

  // 4. 오류 메시지 표시 헬퍼 함수
  function showError(msg) {
    errorAlert.textContent = `⚠️ ${msg}`;
    errorAlert.classList.remove("hidden");
    errorAlert.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  function clearError() {
    errorAlert.textContent = "";
    errorAlert.classList.add("hidden");
  }

  // 5. 폼 제출 이벤트 핸들러
  plannerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearError();

    // 입력값 가져오기
    const goal = document.getElementById("goal").value.trim();
    const examDate = document.getElementById("examDate").value;
    const dailyHours = document.getElementById("dailyHours").value;
    const weakness = document.getElementById("weakness").value.trim();
    const levelElement = document.querySelector('input[name="level"]:checked');
    const styleElement = document.querySelector('input[name="study_style"]:checked');

    const level = levelElement ? levelElement.value : "보통";
    const studyStyle = styleElement ? styleElement.value : "개념 중심";

    // 프론트엔드 유효성 검사 (Validation)
    if (!goal) {
      showError("학습 목표 또는 시험명을 입력해 주세요.");
      return;
    }
    if (!examDate) {
      showError("목표 시험일(D-Day)을 선택해 주세요.");
      return;
    }
    if (!dailyHours || parseFloat(dailyHours) <= 0) {
      showError("하루 가능 학습 시간을 올바르게 입력해 주세요 (최소 0.5시간 이상).");
      return;
    }

    // UI 상태 전환: 폼 숨김 -> 로딩 표시
    formSection.classList.add("hidden");
    loadingSection.classList.remove("hidden");
    resultSection.classList.add("hidden");
    startLoadingAnimation();

    try {
      // Flask Backend /generate 호출
      const response = await fetch("/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          goal: goal,
          exam_date: examDate,
          daily_hours: dailyHours,
          weakness: weakness,
          level: level,
          study_style: studyStyle
        })
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        throw new Error(result.error || "플랜 생성 중 서버 오류가 발생했습니다.");
      }

      // 플랜 렌더링 성공
      renderPlanResult(result);

    } catch (err) {
      console.error("플랜 생성 실패:", err);
      stopLoadingAnimation();
      loadingSection.classList.add("hidden");
      formSection.classList.remove("hidden");
      showError(err.message || "서버와 통신하는 중 문제가 발생했습니다. 잠시 후 다시 시도해 주세요.");
    }
  });

  // 6. 생성된 플랜 화면 렌더링 및 인터랙티브 체크박스 바인딩
  function renderPlanResult(data) {
    stopLoadingAnimation();
    currentRawMarkdown = data.plan_markdown;

    // 배지 업데이트
    badgeTarget.textContent = `🎯 ${data.goal}`;
    badgeDday.textContent = `D-${data.days_left}일`;

    // 마크다운 파싱 및 본문 삽입 (Marked.js 사용)
    planContent.innerHTML = marked.parse(data.plan_markdown);

    // 인터랙티브 체크박스 활성화 작업
    activateCheckboxes();

    // 화면 전환
    loadingSection.classList.add("hidden");
    resultSection.classList.remove("hidden");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  // 7. 체크박스 동적 활성화 및 진도율 트래커 연동
  function activateCheckboxes() {
    const checkboxes = planContent.querySelectorAll('input[type="checkbox"]');

    if (checkboxes.length === 0) {
      // 체크박스가 없는 마크다운인 경우 트래커 숨김
      trackerScore.textContent = "자율 실천 플랜";
      trackerFill.style.width = "100%";
      return;
    }

    // Marked.js가 체크박스에 부여하는 disabled 속성을 제거해 클릭 가능하게 전환
    checkboxes.forEach((cb, index) => {
      cb.removeAttribute("disabled");
      cb.id = `task-cb-${index}`;

      // 클릭 시 취소선 및 진도율 갱신
      cb.addEventListener("change", () => {
        const parentLi = cb.closest("li");
        if (parentLi) {
          if (cb.checked) {
            parentLi.classList.add("task-item-completed");
          } else {
            parentLi.classList.remove("task-item-completed");
          }
        }
        updateProgress(checkboxes);
      });
    });

    // 초기 진도율 0% 계산
    updateProgress(checkboxes);
  }

  // 실시간 진도율 계산 함수
  function updateProgress(checkboxes) {
    const total = checkboxes.length;
    let checkedCount = 0;

    checkboxes.forEach((cb) => {
      if (cb.checked) checkedCount++;
    });

    const percent = total > 0 ? Math.round((checkedCount / total) * 100) : 0;
    trackerScore.textContent = `${checkedCount} / ${total} 완료 (${percent}%)`;
    trackerFill.style.width = `${percent}%`;
  }

  // 8. 클립보드 복사 기능
  copyBtn.addEventListener("click", async () => {
    if (!currentRawMarkdown) return;

    try {
      await navigator.clipboard.writeText(currentRawMarkdown);
      const originalText = copyBtn.innerHTML;
      copyBtn.innerHTML = "✅ 복사 완료!";
      copyBtn.style.backgroundColor = "#dcfce7";

      setTimeout(() => {
        copyBtn.innerHTML = originalText;
        copyBtn.style.backgroundColor = "";
      }, 2000);
    } catch (err) {
      alert("클립보드 복사에 실패했습니다. 브라우저 권한을 확인해 주세요.");
    }
  });

  // 9. 마크다운(.md) 파일 다운로드 기능
  downloadBtn.addEventListener("click", () => {
    if (!currentRawMarkdown) return;

    const blob = new Blob([currentRawMarkdown], { type: "text/markdown;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const today = new Date().toISOString().split("T")[0];

    link.href = url;
    link.download = `AI_Study_Plan_${today}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  });

  // 10. 새로 만들기 버튼 (입력 화면으로 복귀)
  restartBtn.addEventListener("click", () => {
    if (confirm("새로운 플랜을 작성하시겠습니까? 현재 결과는 초기화됩니다.")) {
      resultSection.classList.add("hidden");
      formSection.classList.remove("hidden");
      clearError();
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  });
});

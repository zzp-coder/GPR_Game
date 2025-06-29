// ✅ main.js - 增加暂停功能逻辑
let socket;
let selected = new Set();
let start_time;
let pause_end_time = 0;  // 前端倒计时

function startSocket(username) {
  socket = io();
  socket.emit("join", { username });

  socket.on("start_task", data => {
    // 若处于暂停中，则不更新任务
    if (Date.now() / 1000 < pause_end_time) return;

    if (data.done) {
      window.location.href = "/game-finished";
      return;
    }

    start_time = Date.now() / 1000;

    // ✅ 更新进度条
    const idx = data.current_index || 0;
    const total = data.total || 1;
    document.getElementById("progress-status").innerText = `📘 Progress: ${idx} / ${total}`;
    document.getElementById("progress-bar").value = Math.round((idx / total) * 100);

    // ✅ 显示段落内容
    const box = document.getElementById("paragraph-box");
    box.innerHTML = "";
    selected.clear();
    data.sentences.forEach((sent, idx) => {
      const span = document.createElement("span");
      span.className = "sentence";
      span.dataset.idx = idx;
      span.textContent = sent;
      span.onclick = () => {
        if (span.classList.toggle("selected")) {
          selected.add(idx);
        } else {
          selected.delete(idx);
        }
      };
      box.appendChild(span);
      box.appendChild(document.createTextNode(" "));
    });
    document.getElementById("status").innerText = "🟡 Waiting for your selection...";
  });

  socket.on("waiting_partner", () => {
    document.getElementById("status").innerText = "⏳ Waiting for your partner to come online...";
  });

  socket.on("attempt_failed", data => {
    const msg = `Selections do not match! You have ${data.remaining} attempt(s) left.`;
    document.getElementById("status").innerText = msg;
    alert(msg);
  });

  socket.on("pause_started", data => {
    const seconds = data.seconds;
    const pauseStatus = document.getElementById("pause-status");
    const confirmButton = document.querySelector("button.is-link");

    let remaining = seconds;

    if (pauseStatus) {
      pauseStatus.style.display = "block";
      pauseStatus.innerText = `⏸️ Game paused. Resumes in ${remaining} seconds.`;
    }

    // 禁用“确认”按钮和句子点击
    if (confirmButton) confirmButton.disabled = true;
    document.querySelectorAll(".sentence").forEach(span => span.style.pointerEvents = "none");

    const interval = setInterval(() => {
      remaining -= 1;
      if (pauseStatus) {
        pauseStatus.innerText = `⏸️ Game paused. Resumes in ${remaining} seconds.`;
      }

      if (remaining <= 0) {
        clearInterval(interval);
        if (pauseStatus) pauseStatus.style.display = "none";
        if (confirmButton) confirmButton.disabled = false;
        document.querySelectorAll(".sentence").forEach(span => span.style.pointerEvents = "auto");
      }
    }, 1000);
  });

  updateLeaderboard();
  setInterval(updateLeaderboard, 5000);
}

function submitSelection() {
  socket.emit("submit_selection", {
    username,
    selected: Array.from(selected),
    start_time
  });
  document.getElementById("status").innerText = "⏳ Waiting for partner to confirm...";
}

function updateLeaderboard() {
  fetch("/leaderboard")
    .then(res => res.json())
    .then(data => {
      const board = document.getElementById("leaderboard");
      board.innerHTML = "";
      const maxScore = Math.max(...data.map(d => d[1]), 1);
      const displayMax = maxScore * 1.2;
      const colors = ["#4caf50", "#2196f3", "#ff9800", "#e91e63", "#9c27b0"];

      data.forEach(([user, score], i) => {
        const container = document.createElement("div");
        container.style.margin = "5px 0";

        const label = document.createElement("div");
        label.textContent = `${user}: ${score.toFixed(5)}`;

        const bar = document.createElement("div");
        bar.style.height = "20px";
        bar.style.width = `${Math.min(score / displayMax * 100, 100)}%`;
        bar.style.backgroundColor = colors[i % colors.length];
        bar.style.borderRadius = "5px";
        bar.style.transition = "width 0.3s";

        container.appendChild(label);
        container.appendChild(bar);
        board.appendChild(container);
      });
    });
}

function pauseGame() {
  const minutes = prompt("Pause for how many minutes?", "1");
  if (minutes && !isNaN(minutes) && parseInt(minutes) > 0) {
    socket.emit("pause_request", { minutes: parseInt(minutes) });
  }
}

function countdown(endTime) {
  const el = document.getElementById("pause-status");
  function update() {
    const remaining = Math.max(0, Math.floor(endTime - Date.now() / 1000));
    el.innerText = `⏸️ Game paused. Resumes in ${remaining}s.`;
    if (remaining > 0) setTimeout(update, 1000);
    else el.style.display = "none";
  }
  update();
}

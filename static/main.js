let socket;
let selected = new Set();
let start_time;

function startSocket(username) {
  socket = io();
  socket.emit("join", { username });

  socket.on("start_task", data => {
    start_time = Date.now() / 1000;
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
    document.getElementById("status").innerText = "Waiting for your selection...";
  });

  // ✅ 新增：响应匹配失败事件
  socket.on("attempt_failed", data => {
    const msg = `Selections do not match! You have ${data.remaining} attempt(s) left.`;
    document.getElementById("status").innerText = msg;
    alert(msg);
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
  document.getElementById("status").innerText = "Waiting for partner to confirm...";
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
        label.textContent = `${user}: ${score.toFixed(1)}`;

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
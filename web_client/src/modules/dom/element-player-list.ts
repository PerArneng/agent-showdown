import type { PlayerList } from "../../interfaces/dom/index.js";
import type { PlayerState } from "../../interfaces/game/index.js";
import { spriteUrlFor } from "../canvas/sprites.js";

/** Edge module. Writes the roster and statistics into the document. */
export class ElementPlayerList implements PlayerList {
  constructor(
    private readonly element: HTMLElement,
    private readonly document: Document,
  ) {}

  show(players: readonly PlayerState[], thinking: string | null = null): void {
    if (players.length === 0) {
      this.element.replaceChildren(this.empty());
      return;
    }

    const maxThink = Math.max(...players.map((p) => p.thinkSeconds), 0.1);

    const table = this.document.createElement("table");
    table.className = "stats-table";

    const thead = this.document.createElement("thead");
    const headerRow = this.document.createElement("tr");

    const columns = [
      { key: "agent", label: "Agent" },
      { key: "status", label: "Status" },
      { key: "health", label: "Health" },
      { key: "pos", label: "Position" },
      { key: "last-turn", label: "Last Turn" },
      { key: "avg-turn", label: "Avg Turn" },
      { key: "total-time", label: "Total Time" },
      { key: "turns", label: "Turns" },
      { key: "eliminations", label: "Kills" },
      { key: "deaths", label: "Deaths" },
      { key: "wins", label: "Wins" },
      { key: "plan", label: "Latest Reasoning" },
    ];

    for (const col of columns) {
      const th = this.document.createElement("th");
      th.className = `col-${col.key}`;
      th.textContent = col.label;
      headerRow.append(th);
    }
    thead.append(headerRow);

    const tbody = this.document.createElement("tbody");
    for (const player of players) {
      tbody.append(this.row(player, thinking === player.name, maxThink));
    }

    table.append(thead, tbody);
    this.element.replaceChildren(table);
  }

  private empty(): HTMLElement {
    const emptyDiv = this.document.createElement("div");
    emptyDiv.className = "empty-roster";
    emptyDiv.textContent = "No contestants yet. Start a game to see agent timing & statistics.";
    return emptyDiv;
  }

  private row(player: PlayerState, isThinking: boolean, maxThink: number): HTMLElement {
    const isDead = player.health <= 0;
    const tr = this.document.createElement("tr");
    tr.className = `player-row${isThinking ? " is-thinking" : ""}${isDead ? " is-dead" : ""}`;

    // 1. Agent column (avatar + swatch + name)
    const tdAgent = this.document.createElement("td");
    tdAgent.className = "cell-agent";

    const avatar = this.document.createElement("img");
    avatar.className = "sprite-avatar";
    avatar.src = spriteUrlFor(player.sprite);
    avatar.alt = `Robot #${player.sprite}`;
    avatar.width = 24;
    avatar.height = 24;

    const swatch = this.document.createElement("span");
    swatch.className = "swatch";
    swatch.style.background = player.color;

    const name = this.document.createElement("span");
    name.className = "player-name";
    name.textContent = player.name;

    tdAgent.append(avatar, swatch, name);

    // 2. Status column
    const tdStatus = this.document.createElement("td");
    tdStatus.className = "cell-status";

    const statusBadge = this.document.createElement("span");
    if (isDead) {
      statusBadge.className = "status-badge defeated";
      statusBadge.textContent = "💀 Defeated";
    } else if (isThinking) {
      statusBadge.className = "status-badge thinking";
      const dot = this.document.createElement("span");
      dot.className = "pulse-dot";
      const text = this.document.createElement("span");
      text.textContent = "Thinking";
      statusBadge.append(dot, text);
    } else if (player.turnsPlayed > 0) {
      statusBadge.className = "status-badge idle";
      statusBadge.textContent = "Idle";
    } else {
      statusBadge.className = "status-badge ready";
      statusBadge.textContent = "Ready";
    }
    tdStatus.append(statusBadge);

    // 3. Health column
    const tdHealth = this.document.createElement("td");
    tdHealth.className = "cell-health";

    const healthText = this.document.createElement("span");
    healthText.className = "health-val";
    healthText.textContent = `${player.health}/100`;

    const healthBarTrack = this.document.createElement("div");
    healthBarTrack.className = "health-bar-track";

    const healthBarFill = this.document.createElement("div");
    const hpPercent = Math.max(0, Math.min(100, player.health));
    const hpClass =
      hpPercent > 50 ? "hp-high" : hpPercent > 25 ? "hp-mid" : hpPercent > 0 ? "hp-low" : "hp-dead";
    healthBarFill.className = `health-bar-fill ${hpClass}`;
    healthBarFill.style.width = `${hpPercent}%`;

    healthBarTrack.append(healthBarFill);
    tdHealth.append(healthText, healthBarTrack);

    // 4. Position column
    const tdPos = this.document.createElement("td");
    tdPos.className = "cell-pos";
    tdPos.textContent = `(${player.position.x}, ${player.position.y})`;

    // 5. Last Turn column
    const tdLastTurn = this.document.createElement("td");
    tdLastTurn.className = "cell-last-turn";

    if (player.thinkSeconds > 0) {
      const timeVal = this.document.createElement("span");
      timeVal.className = "think-time-val";
      timeVal.textContent = `${player.thinkSeconds.toFixed(2)}s`;

      const barContainer = this.document.createElement("div");
      barContainer.className = "think-bar-track";

      const barFill = this.document.createElement("div");
      barFill.className = "think-bar-fill";
      const percentage = Math.min(
        100,
        Math.max(10, Math.round((player.thinkSeconds / maxThink) * 100)),
      );
      barFill.style.width = `${percentage}%`;
      barFill.style.backgroundColor = player.color;

      barContainer.append(barFill);
      tdLastTurn.append(timeVal, barContainer);
    } else {
      tdLastTurn.textContent = "-";
    }

    // 6. Avg Turn column
    const tdAvg = this.document.createElement("td");
    tdAvg.className = "cell-avg-turn";
    if (player.turnsPlayed > 0) {
      tdAvg.textContent = `${player.averageThinkSeconds.toFixed(2)}s`;
    } else {
      tdAvg.textContent = "-";
    }

    // 7. Total Time column
    const tdTotal = this.document.createElement("td");
    tdTotal.className = "cell-total-time";
    tdTotal.textContent = player.turnsPlayed > 0 ? `${player.totalThinkSeconds.toFixed(1)}s` : "-";

    // 8. Turns count column
    const tdTurns = this.document.createElement("td");
    tdTurns.className = "cell-turns";
    tdTurns.textContent = `${player.turnsPlayed}`;

    // 9. Eliminations column
    const tdElims = this.document.createElement("td");
    tdElims.className = "cell-elims";
    tdElims.innerHTML = `<span class="stat-badge elims"><span aria-hidden="true">⚔️</span> ${player.eliminations}</span>`;

    // 10. Deaths column
    const tdDeaths = this.document.createElement("td");
    tdDeaths.className = "cell-deaths";
    tdDeaths.innerHTML = `<span class="stat-badge deaths"><span aria-hidden="true">💀</span> ${player.deaths}</span>`;

    // 11. Wins column
    const tdWins = this.document.createElement("td");
    tdWins.className = "cell-wins";
    tdWins.innerHTML = `<span class="stat-badge wins"><span aria-hidden="true">🏆</span> ${player.wins}</span>`;

    // 12. Reasoning / plan column
    const tdReasoning = this.document.createElement("td");
    tdReasoning.className = "cell-reasoning";
    if (player.reasoning) {
      const reasoningSpan = this.document.createElement("span");
      reasoningSpan.className = "reasoning-text";
      reasoningSpan.textContent = `“${player.reasoning}”`;
      reasoningSpan.title = player.reasoning;
      tdReasoning.append(reasoningSpan);
    } else {
      tdReasoning.textContent = "-";
    }

    tr.append(
      tdAgent,
      tdStatus,
      tdHealth,
      tdPos,
      tdLastTurn,
      tdAvg,
      tdTotal,
      tdTurns,
      tdElims,
      tdDeaths,
      tdWins,
      tdReasoning,
    );
    return tr;
  }
}

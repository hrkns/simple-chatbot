async function hydrateUI() {
  try {
    const res = await fetch("/config.json");
    if (!res.ok) throw new Error("config fetch failed");
    const config = await res.json();

    if (config.title)
      document.querySelector('title[data-bind="title"]').textContent =
        config.title;

    if (config.heading)
      document.querySelector('[data-bind="heading"]').textContent =
        config.heading;

    if (config.placeholder)
      document
        .querySelector('[data-bind="placeholder"]')
        .setAttribute("placeholder", config.placeholder);
  } catch (err) {
    console.warn("Using default UI text –", err);
  }
}
hydrateUI();

const endpoint = "/chat/invoke";
const log = document.getElementById("log");

const exchanges = []

let sending = false;

document.getElementById("form").addEventListener("submit", async (e) => {
  e.preventDefault();

  if (sending) {
    return;
  }

  sending = true;

  const question = document.getElementById("q").value;
  log.textContent = "You: " + question + "\n\n" + log.textContent;

  const exchange = {
    question: question,
    answer: '.'
  }
  exchanges.unshift(exchange)

  const interval = setInterval(() => {
    if (exchange.answer.length === 3) {
      exchange.answer = "."
    } else {
      exchange.answer += "."
    }
    log.textContent = exchanges.map((exchange) => {
      return "You: " + exchange.question + "\n\n" + "Bot: " + exchange.answer + "\n\n"
    }).join("")
  }, 300);

  const res = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ input: { question, chat_history: [] } }),
  });

  clearInterval(interval);

  const data = await res.json();
  exchange.answer = data.output.answer
  log.textContent = exchanges.map((exchange) => {
    return "You: " + exchange.question + "\n\n" + "Bot: " + exchange.answer + "\n\n"
  }).join("")
  document.getElementById("q").value = "";
  sending = false;
});

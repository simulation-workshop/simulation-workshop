# Introduction to System Simulation

<div class="quiz-container" style="border: 1px solid var(--border-color); padding: 20px; border-radius: 8px; margin: 20px 0;">
  <h3>Quick Quiz: What is the primary benefit of static site generators?</h3>
  <form id="quiz-1">
    <label><input type="radio" name="q1" value="wrong"> Slower load times</label><br>
    <label><input type="radio" name="q1" value="correct"> Blazing fast speed & high security</label><br>
    <label><input type="radio" name="q1" value="wrong"> Requires a heavy database</label><br><br>
    <button type="button" onclick="checkAnswer()" style="padding: 6px 12px; cursor: pointer;">Submit Answer</button>
  </form>
  <p id="quiz-result" style="font-weight: bold; margin-top: 10px;"></p>
</div>

<script>
function checkAnswer() {
  const selected = document.querySelector('input[name="q1"]:checked');
  const result = document.getElementById('quiz-result');
  if (!selected) {
    result.style.color = "orange";
    result.textContent = "Please select an option first!";
    return;
  }
  if (selected.value === "correct") {
    result.style.color = "green";
    result.textContent = "Correct! Static sites don't rely on server-side databases.";
  } else {
    result.style.color = "red";
    result.textContent = "Incorrect. Try again!";
  }
}
</script>
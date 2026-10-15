const form = document.querySelector("#charter-form")
const idInput = document.querySelector("#cid")
let idTouched = false

idInput.addEventListener("input", () => {
  idTouched = true
  render()
})

form.addEventListener("input", render)
form.addEventListener("submit", (event) => {
  event.preventDefault()
  const charter = read()
  const warn = document.querySelector("#form-warn")
  if (!charter) {
    warn.textContent = "Add a name, a short link name, and why someone should contribute."
    return
  }
  warn.textContent = ""
  const blob = new Blob([JSON.stringify(charter, null, 2) + "\n"], { type: "application/json" })
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = charter.id + ".charter.json"
  link.click()
  URL.revokeObjectURL(url)
})

document.querySelector("#copy-link").addEventListener("click", async () => {
  const charter = read()
  const warn = document.querySelector("#form-warn")
  if (!charter) {
    warn.textContent = "Add a name and why someone should contribute first."
    return
  }
  const link = "banner://join/" + charter.id
  try {
    await navigator.clipboard.writeText(link)
    warn.textContent = "Copied " + link
  } catch {
    warn.textContent = link
  }
})

function slug(value) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 32)
    .replace(/-+$/g, "")
}

function field(id) {
  return document.querySelector("#" + id).value.trim()
}

function read() {
  const name = field("name")
  const id = slug(field("cid"))
  const pitch = field("pitch")
  if (!name || !id || !/^[a-z][a-z0-9-]{0,31}$/.test(id) || !pitch) return null
  const goals = field("goals").split("\n").map((line) => line.trim()).filter(Boolean)
  return {
    id,
    name,
    summary: field("summary"),
    pitch,
    goals,
    work: field("work"),
    done_when: field("done"),
    join: "banner://join/" + id,
  }
}

function text(id, value, empty) {
  const node = document.querySelector("#" + id)
  node.textContent = value || empty || ""
}

function render() {
  if (!idTouched) {
    const next = slug(field("name"))
    if (next) idInput.value = next
  }
  const name = field("name") || "Your project"
  const id = slug(field("cid")) || "your-project"
  text("preview-name", name)
  text("preview-summary", field("summary"))
  text("preview-pitch", field("pitch"))
  text("preview-work", field("work"))
  text("preview-id", id)
  text("join-preview", "banner://join/" + id)
  const list = document.querySelector("#preview-goals")
  list.replaceChildren()
  field("goals").split("\n").map((line) => line.trim()).filter(Boolean).forEach((goal) => {
    const item = document.createElement("li")
    item.textContent = goal
    list.appendChild(item)
  })
}

render()

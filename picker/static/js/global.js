let view
let collName
let clearCollButton

window.addEventListener("load", () => {
	viewLabel = window.location.pathname.split('/').slice(-1)

	if (viewLabel == "list" || viewLabel == "cards") {
		view = viewLabel
		
		collName = document.getElementById("collection-faceted-name").innerText
		// clearCollButton not shown if user isn't admin, error in JS console
		clearCollButton = document.getElementById("clear-collection")

		window.addEventListener("beforeunload", () => {
			fetch("/auth/clearbooking")
				.then((response) => response.json())
				.then((data) => console.log(data))
		})

		clearCollButton.addEventListener("click", () => {
			clearCollButtonWarning()
		})

	} else {
		view = "home"
	}
})

async function changeProject(projectId) {
	let data = new FormData()
	data.set("projectId", projectId)
	let response = await fetch("/auth/projectselection", {
		method: "POST",
		body: data,
	});

	let result = await response.json()
	let oldProjectId = result["old-proj-id"]
	let newProjectId = result["new-proj-id"]
	let newProjectTitle = result["new-proj-title"]
	let projectDropdown = document.getElementById("proj-dropdown")

	if (oldProjectId != null) {
		oldProjectSelectedNode = document.getElementById("proj-" + oldProjectId)
		oldProjectSelectedNode.removeAttribute("disabled")
		oldProjectSelectedNode.setAttribute("onclick", "changeProject(" + oldProjectId + ")")
	}

	newProjectSelectedNode = document.getElementById("proj-" + newProjectId)
	newProjectSelectedNode.removeAttribute("onclick")
	newProjectSelectedNode.setAttribute("disabled", "")

	projectDropdown.innerText = newProjectTitle

	if (view == "list") {
		setCurrentPage(1)
	} else if (view == "cards") {
		getCards()
	}
}

async function clearCollButtonWarning() {
	clearCollButton.classList.remove("btn-warning")
	clearCollButton.classList.add("btn-danger")
	clearCollButton.innerText = "Really delete selections?"
	await new Promise(resolve => setTimeout(resolve, 1000))
	clearCollButton.setAttribute("href", "/view/" + collName + "/clearcollection")
}
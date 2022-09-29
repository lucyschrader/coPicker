async function saveSelection(url, irn, selection) {
	let data = new FormData()
	data.set("irn", irn)
	data.set("selection", selection)
	let response = await fetch(url, {
		method: "POST",
		body: data,
	});

	let result = await response.json()
	let yn = result.include

	let button = document.getElementById("select-" + irn + "-" + yn)
	if (yn == "y") {
		let otherButton = document.getElementById("select-" + irn + "-n")
		button.classList.add("active")
		otherButton.classList.remove("active")
		}
	else if (yn == "n") {
		let otherButton = document.getElementById("select-" + irn + "-y")
		button.classList.add("active")
		otherButton.classList.remove("active")
		}
	console.log(irn + " was successfully updated")
	}
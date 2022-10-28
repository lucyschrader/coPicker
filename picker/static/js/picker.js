let paginationList;
let prevButton;
let nextButton;
let cardDiv;

let filterToD;

let filterToDoStatus = false;

let collSize;
const paginationLimit = 30;
let pageCount;

let currentPage;

const getPaginationNumbers = () => {
	appendPreviousButton();
	for (let i = 1; i <= pageCount; i++) {
		appendPageNumber(i);
	};
	appendNextButton();
};

const appendPreviousButton = () => {
	const prevButton = document.createElement("li");
	prevButton.className = "page-item";
	prevButton.setAttribute("id", "pageprev");

	const prevButtonLink = document.createElement("a");
	prevButtonLink.className = "page-link";
	prevButtonLink.setAttribute("href", "#");
	prevButtonLink.innerText = "Previous";

	prevButton.appendChild(prevButtonLink);
	paginationList.appendChild(prevButton);
}

const appendNextButton = () => {
	const nextButton = document.createElement("li");
	nextButton.className = "page-item";
	nextButton.setAttribute("id", "pagenext");

	const nextButtonLink = document.createElement("a");
	nextButtonLink.className = "page-link";
	nextButtonLink.setAttribute("href", "#");
	nextButtonLink.innerText = "Next";

	nextButton.appendChild(nextButtonLink);
	paginationList.appendChild(nextButton);
}

const appendPageNumber = (index) => {
	const pageNumber = document.createElement("li");
	pageNumber.className = "page-item";
	pageNumber.setAttribute("page-index", index);
	pageNumber.setAttribute("aria-label", "Page " + index);

	const pageNumberLink = document.createElement("a");
	pageNumberLink.className = "page-link";
	pageNumberLink.setAttribute("href", "#");
	pageNumberLink.innerText = index;
	pageNumber.appendChild(pageNumberLink);

	paginationList.appendChild(pageNumber);
};

const handleActivePageNumber = () => {
	document.querySelectorAll(".page-item").forEach((button) => {
		button.classList.remove("active");

		const pageIndex = Number(button.getAttribute("page-index"));
		
		if (pageIndex == currentPage) {
			button.classList.add("active");
		}
	});
};

const disableButton = (button) => {
	button.classList.add("disabled");
	button.setAttribute("disabled", true);
};

const enableButton = (button) => {
	button.classList.remove("disabled");
	button.removeAttribute("disabled", true);
};

const filterOn = (button) => {
	button.classList.add("btn-primary");
	button.classList.remove("btn-secondary");
	button.innerText = "Click to see all items";
	filterToDoStatus = true;
};

const filterOff = (button) => {
	button.classList.add("btn-secondary");
	button.classList.remove("btn-primary");
	button.innerText = "Click to see items needing checking";
	filterToDoStatus = false;
};

const handlePageButtonStatus = () => {
	if (currentPage === 1) {
		disableButton(prevButton);
	} else if (prevButton.classList.contains("disabled")) {
		enableButton(prevButton);
	}

	if (pageCount === currentPage) {
		disableButton(nextButton);
	} else if (nextButton.classList.contains("disabled")) {
		enableButton(nextButton);
	};
};

window.addEventListener("load", () => {
	paginationList = document.getElementById("pagepick");
	cardDiv = document.getElementById("record-cards");

	filterToDo = document.getElementById("filter-todo");

	collSize = document.getElementById("coll-size").innerText;

	pageCount = Math.ceil(collSize / paginationLimit);

	getPaginationNumbers();

	prevButton = document.getElementById("pageprev");
	nextButton = document.getElementById("pagenext");

	setCurrentPage(1);

	filterToDo.addEventListener("click", () => {
		if (filterToDoStatus == false) {
			filterOn(filterToDo);
		} else {
			filterOff(filterToDo);
		};
		setCurrentPage(1);
	})

	prevButton.addEventListener("click", () => {
		setCurrentPage(currentPage - 1);
	});

	nextButton.addEventListener("click", () => {
		setCurrentPage(currentPage + 1);
	});

	document.querySelectorAll(".page-item").forEach((button) => {
		const pageIndex = Number(button.getAttribute("page-index"));

		if (pageIndex) {
			button.addEventListener("click", () => {
				setCurrentPage(pageIndex);
			});
		}
	});
});

async function setCurrentPage(pageNum) {
	currentPage = pageNum;

	handleActivePageNumber();
	handlePageButtonStatus();

	const startNo = (pageNum - 1) * paginationLimit;
	const currRange = pageNum * paginationLimit;
	const collName = window.location.pathname.split('/').slice(-1);

	let data = new FormData
	data.set("start", startNo)
	data.set("size", paginationLimit)
	data.set("todo", filterToDoStatus)

	let response = await fetch("/view/" + collName, {
		method: "POST",
		body: data,
	});

	let newCards = await response.json()
	console.log(newCards)

	if (newCards == "none") {
		cardDiv.innerHTML = ""
		cardDiv.innerHTML = "<p>No matching images.</p>"
	} else {
		let cardsHtml = ""

		newCards.forEach((card) => {
			cardsHtml += card
		})

		cardDiv.innerHTML = ""
		cardDiv.innerHTML = cardsHtml
	};
};

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
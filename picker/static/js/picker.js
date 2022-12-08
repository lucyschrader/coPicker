let paginationList;
let prevButton;
let nextButton;
let cardDiv;
let listDiv;
let listUl;
let modalsDiv;

let filterToDo;
let filterToDoStatus = false;

let filterIncluded;
let filterIncludedStatus = false;

let filterExcluded;
let filterExcludedStatus = false;

let sortByModified;
let sortByModifiedStatus = false;

let collSize;
const paginationLimit = 40;
const cardLimit = 4;
let cardCountdown;
let pageCount;

let recCheckedCount;
let recIncCount;
let totalImgCount;
let imgIncCount;
let imgExcCount;

let currentPage;

window.addEventListener("load", () => {
	collSize = document.getElementById("coll-size").innerText;
	recCheckedCount = document.getElementById("recs-checked")
	recIncCount = document.getElementById("recs-with-inclusions")
	totalImgCount = document.getElementById("total-img-count")
	imgIncCount = document.getElementById("img-included")
	imgExcCount = document.getElementById("img-excluded")

	if (view == "list") {
		paginationList = document.getElementById("pagepick");
		listDiv = document.getElementById("record-list")
		listUl = document.getElementById("record-ul");
		modalsDiv = document.getElementById("record-modals");
		filterToDo = document.getElementById("filter-todo");
		filterIncluded = document.getElementById("filter-included")
		filterExcluded = document.getElementById("filter-excluded")
		sortByModified = document.getElementById("sort-new")
		pageCount = Math.ceil(collSize / paginationLimit);

		getPaginationNumbers();

		prevButton = document.getElementById("pageprev");
		nextButton = document.getElementById("pagenext");

		setCurrentPage(1);

		filterToDo.addEventListener("click", () => {
			if (filterToDoStatus == false) {
				filterToDoStatus = true;
				filterOn(filterToDo, "See all records");
				filterIncludedStatus = false;
				filterOff(filterIncluded, "See records with inclusions");
				filterExcludedStatus = false;
				filterOff(filterExcluded, "See excluded records");
			} else {
				filterToDoStatus = false;
				filterOff(filterToDo, "See records needing checking");
			};
			setCurrentPage(1);
		})

		filterIncluded.addEventListener("click", () => {
			if (filterIncludedStatus == false) {
				filterIncludedStatus = true;
				filterOn(filterIncluded, "See all records");
				filterToDoStatus = false;
				filterOff(filterToDo, "See records needing checking");
				filterExcludedStatus = false;
				filterOff(filterExcluded, "See excluded records");
			} else {
				filterIncludedStatus = false;
				filterOff(filterIncluded, "See records with inclusions");
			};
			setCurrentPage(1);
		})

		filterExcluded.addEventListener("click", () => {
			if (filterExcludedStatus == false) {
				filterExcludedStatus = true;
				filterOn(filterExcluded, "See all records");
				filterToDoStatus = false;
				filterOff(filterToDo, "See records needing checking");
				filterIncludedStatus = false;
				filterOff(filterIncluded, "See records with inclusions");
			} else {
				filterExcludedStatus = false;
				filterOff(filterExcluded, "See excluded records");
			};
			setCurrentPage(1);
		})

		sortByModified.addEventListener("click", () => {
			if (sortByModifiedStatus == false) {
				sortByModifiedStatus = true;
				filterOn(sortByModified, "Sort by IRN");
			} else {
				sortByModifiedStatus = false;
				filterOff(sortByModified, "Sort by last modified");
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

	} else {
		view = "cards"

		cardDiv = document.getElementById("record-cards");

		getCards()
	}	
});

async function setCurrentPage(pageNum) {
	currentPage = pageNum;
	const collName = document.getElementById("collection-faceted-name").innerText;

	let data = new FormData
	data.set("current-page", currentPage)
	data.set("size", paginationLimit)
	data.set("filter-todo", filterToDoStatus)
	data.set("filter-included", filterIncludedStatus)
	data.set("filter-excluded", filterExcludedStatus)
	data.set("sort-new", sortByModifiedStatus)
	data.set("view", "list")

	let response = await fetch("/view/" + collName + "/page", {
		method: "POST",
		body: data,
	});

	let responseJson = await response.json()

	let recordData = responseJson["recordData"]
	let listBlocks = responseJson["htmlBlocks"]

	let listItems = listBlocks["items"]
	let listModals = listBlocks["modals"]
	let pageCount = listBlocks["page-count"]

	setOnLoadCounts(recordData)
	
	getPaginationNumbers()

	handleActivePageNumber();
	handlePageButtonStatus();
	hideExtraPageNumbers();

	if (listItems.length > 0) {
		let listHtml = ""

		listItems.forEach((item) => {
			listHtml += item
		})

		listUl.innerHTML = listHtml

		let listModalHtml = ""

		listModals.forEach((modal) => {
			listModalHtml += modal
		})

		modalsDiv.innerHTML = listModalHtml
	} else {
		listUl.innerHTML = "<li class='list-group-item'>No matching images.</li>"
	};
};

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

const filterOn = (button, message) => {
	button.classList.add("active");
	button.innerText = message;
};

const filterOff = (button, message) => {
	button.classList.remove("active");
	button.innerText = message;
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

const hideExtraPageNumbers = () => {
	let paginationElements = document.querySelectorAll("li[page-index]")

	for (let i = 2; i < pageCount; i++) {
		if (i < currentPage - 3 || i > currentPage + 3) {
			paginationElement = document.querySelector("li[page-index='" + i + "']")
			paginationElement.hidden = true;
		}
	}
}

async function getCards() {
	const collName = document.getElementById("collection-faceted-name").innerText;

	let data = new FormData
	data.set("start", 0)
	data.set("size", cardLimit)
	data.set("filter-todo", null)
	data.set("filter-included", null)
	data.set("filter-excluded", null)
	data.set("sort-new", null)
	data.set("view", "cards")

	let response = await fetch("/view/" + collName + "/page", {
		method: "POST",
		body: data
	});

	let responseJson = await response.json()
	console.log(responseJson)

	let recordData = responseJson["recordData"]
	let cardBlocks = responseJson["htmlBlocks"]

	setOnLoadCounts(recordData)

	if (cardBlocks == "none") {
		cardDiv.innerHTML = "<p>No matching images.</p>"
	} else if (cardBlocks.length == 0) {
		cardDiv.innerHTML = "<p>All out of images.</p>"
	} else {
		cardCountdown = cardBlocks.length
		let cardsHtml = ""

		cardBlocks.forEach((card) => {
			cardsHtml += card
		})

		cardDiv.innerHTML = cardsHtml
	};
}

const setOnLoadCounts = (recordData) => {
	collSize.innerText = recordData.total_records
	recCheckedCount.innerText = recordData.recs_checked
	recIncCount.innerHTML = recordData.recs_with_inclusions
	totalImgCount.innerText = recordData.total_images
	imgIncCount.innerHTML = recordData.img_included
	imgExcCount.innerHTML = recordData.img_excluded
}

async function saveSelection(url, record_irn, media_irn, selection, mode) {
	let data = new FormData()
	data.set("record_irn", record_irn)
	data.set("media_irn", media_irn)
	data.set("selection", selection)
	let response = await fetch(url, {
		method: "POST",
		body: data,
	});

	let result = await response.json()

	console.log(media_irn + " was successfully updated")

	updateCompleteCount(result)
	updateIncludeExcludeCounts(result)
	updateRecIncludeCount(result)

	if (mode == "modal") {
		updateModalSelection(media_irn, result)
	}

	updateSelection(record_irn, result)
	
	if (view == "cards") {
		if (cardCountdown == 0) {
			finishCardSet(record_irn)
		}
	} else if (view == "list") {
		let newRecInclude = result.new_rec_status_include

		let recordBadge = document.getElementById("badge-" + record_irn)
		let icon = recordBadge.firstElementChild

		if (newRecInclude == "y") {
			recordBadge.classList.add("text-bg-primary")
			icon.setAttribute("src", "/static/images/check-circle.svg")
			if (recordBadge.classList.contains("text-bg-warning")) {
				recordBadge.classList.remove("text-bg-warning")
			}
			if (recordBadge.classList.contains("text-bg-secondary")) {
				recordBadge.classList.remove("text-bg-secondary")
			}
		} else if (newRecInclude == "n") {
			recordBadge.classList.add("text-bg-warning")
			icon.setAttribute("src", "/static/images/x-circle.svg")
			if (recordBadge.classList.contains("text-bg-primary")) {
				recordBadge.classList.remove("text-bg-primary")
			}
			if (recordInclude.classList.contains("text-bg-secondary")) {
				recordBadge.classList.remove("text-bg-secondary")
			}
		}
	}
}

const updateCompleteCount = (result) => {
	console.log("Updating count!")
	let prevRecComplete = result.prev_rec_status_complete
	let newRecComplete = result.new_rec_status_complete

	let recCheckedCountNum = parseInt(recCheckedCount.innerText);

	if (prevRecComplete == null) {
		if (newRecComplete == "y") {
			recCheckedCountNum += 1;
			recCheckedCount.innerText = recCheckedCountNum;

			cardCountdown -= 1;
			console.log(cardCountdown);
		}
	}
}

const updateIncludeExcludeCounts = (result) => {
	let yn = result.new_include
	let prevSelection = result.prev_include

	let imgIncCountNum = parseInt(imgIncCount.innerText);
	let imgExcCountNum = parseInt(imgExcCount.innerText);

	if (yn == "y") {
		imgIncCountNum += 1;
		imgIncCount.innerText = imgIncCountNum;
		if (prevSelection == "n") {
			imgExcCountNum -= 1;
			imgExcCount.innerText = imgExcCountNum;
		}
	} else if (yn == "n") {
		imgExcCountNum += 1;
		imgExcCount.innerText = imgExcCountNum;
		if (prevSelection == "y") {
			imgIncCountNum -= 1;
			imgIncCount.innerText = imgIncCountNum;
		}
	}
}

const updateRecIncludeCount = (result) => {
	let yn = result.new_include
	let prevSelection = result.prev_include
	let prevRecInclude = result.prev_rec_status_include
	let newRecInclude = result.new_rec_status_include

	let recIncCountNum = parseInt(recIncCount.innerText);

	if (prevRecInclude == null) {
		if (newRecInclude == "y") {
			recIncCountNum += 1
			recIncCount.innerText = recIncCountNum
		}
	} else if (prevRecInclude == "n") {
		if (newRecInclude == "y") {
			recIncCountNum += 1
			recIncCount.innerText = recIncCountNum
		}
	} else if (prevRecInclude == "y") {
		if (newRecInclude == "n") {
			recIncCountNum -= 1
			recIncCount.innerText = recIncCountNum
		}
	}
}

const updateModalSelection = (media_irn, result) => {
	let yn = result.new_include

	let imageBlock = document.getElementById("block-" + media_irn)
	let imageSelectionIndicator = imageBlock.querySelector(".select-indicator")

	if (yn == "y") {
		imageSelectionIndicator.classList.remove("indicate-none")
		imageSelectionIndicator.classList.remove("indicate-exclude")
		imageSelectionIndicator.classList.add("indicate-include")
	} else if (yn == "n") {
		imageSelectionIndicator.classList.remove("indicate-none")
		imageSelectionIndicator.classList.remove("indicate-include")
		imageSelectionIndicator.classList.add("indicate-exclude")
	}
}

const updateSelection = (record_irn, result) => {
	let yn = result.new_include
	let prevSelection = result.prev_include
	let prevRecInclude = result.prev_rec_status_include
	let newRecInclude = result.new_rec_status_include

	let recordCard = document.getElementById("card-" + record_irn)
	let cardSelectionIndicator = recordCard.querySelector(".select-indicator")

	if (prevRecInclude == null) {
		if (newRecInclude == "y") {
			cardSelectionIndicator.classList.remove("indicate-none")
			cardSelectionIndicator.classList.add("indicate-include")
		} else if (newRecInclude == "n") {
			cardSelectionIndicator.classList.remove("indicate-none")
			cardSelectionIndicator.classList.add("indicate-exclude")
		}
	} else if (prevRecInclude == "n") {
		if (newRecInclude == "y") {
			cardSelectionIndicator.classList.remove("indicate-exclude")
			cardSelectionIndicator.classList.add("indicate-include")
		}
	} else if (prevRecInclude == "y") {
		if (newRecInclude == "n") {
			cardSelectionIndicator.classList.remove("indicate-include")
			cardSelectionIndicator.classList.add("indicate-exclude")
		}
	}
}

async function selectAllModal(recordIrn, recordMedia, selection) {
	let url = "/view/select"

	console.log(recordMedia)

	for (let i = 0; i < recordMedia.length; i++) {
		await saveSelection(url, recordIrn, recordMedia[i], selection, 'modal')
	}
}

const finishCardSet = (recordIrn) => {
	const modal = document.querySelector("#select-modal-" + recordIrn)
	if (modal.classList.contains("show")) {
		const openModal = bootstrap.Modal.getInstance(modal)
		openModal.hide()
		modal.addEventListener("hidden.bs.modal", () => {
			openModal.dispose();
		}, {once:true});
	}
	cardDiv.innerHTML = ""
	cardDiv.innerHTML = "<div class='d-flex justify-content-center'><div class='spinner-border' role='status'><span class='visually-hidden'>Loading...</span></div></div>"
	getCards()
}
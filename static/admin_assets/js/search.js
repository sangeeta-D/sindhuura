
document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById("userSearch");
  const tableRows = Array.from(document.querySelectorAll("tbody tr"));
  const pagination = document.getElementById("pagination");

  const rowsPerPage = 8;
  let currentPage = 1;
  let filteredRows = tableRows;

  function renderTable() {
    tableRows.forEach(row => row.style.display = "none");

    const start = (currentPage - 1) * rowsPerPage;
    const end = start + rowsPerPage;

    filteredRows.slice(start, end).forEach(row => {
      row.style.display = "";
    });

    renderPagination();
  }

  function renderPagination() {
    pagination.innerHTML = "";
    const totalPages = Math.ceil(filteredRows.length / rowsPerPage);

    for (let i = 1; i <= totalPages; i++) {
      const li = document.createElement("li");
      li.className = `page-item ${i === currentPage ? "active" : ""}`;

      const a = document.createElement("a");
      a.className = "page-link";
      a.href = "#";
      a.textContent = i;

      a.addEventListener("click", function (e) {
        e.preventDefault();
        currentPage = i;
        renderTable();
      });

      li.appendChild(a);
      pagination.appendChild(li);
    }
  }

  searchInput.addEventListener("keyup", function () {
    const query = this.value.toLowerCase();

    filteredRows = tableRows.filter(row =>
      row.innerText.toLowerCase().includes(query)
    );

    currentPage = 1;
    renderTable();
  });

  renderTable();
});

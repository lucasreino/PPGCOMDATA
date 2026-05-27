from app.services.scholar_profile_parser import parse_scholar_profile_html

SAMPLE_HTML = """
<!-- saved from url=(0066)https://scholar.google.com/citations?user=TESTUSER1&hl=pt-BR -->
<html><head>
<meta property="og:title" content="Autor Teste">
<meta property="og:description" content="UFMA - Citado por 42 - Jornalismo">
</head><body>
<table id="gsc_rsb_st">
<tr class="gsc_rsb_sth"><th></th><th>Todos</th><th>Desde 2020</th></tr>
<tr><td class="gsc_rsb_sc1">Citações</td>
<td class="gsc_rsb_std">42</td><td class="gsc_rsb_std">10</td></tr>
<tr><td class="gsc_rsb_sc1">Índice h</td>
<td class="gsc_rsb_std">3</td><td class="gsc_rsb_std">2</td></tr>
<tr><td class="gsc_rsb_sc1">Índice i10</td>
<td class="gsc_rsb_std">1</td><td class="gsc_rsb_std">0</td></tr>
</table>
<tr class="gsc_a_tr">
<td><a class="gsc_a_at">Artigo A</a>
<div class="gs_gray">A Silva</div>
<div class="gs_gray">Revista X, 2019</div></td>
<td class="gsc_a_y"><span class="gsc_a_h gsc_a_hc gs_ibl">2019</span></td>
<td class="gsc_a_c gsc_a_cg"><span class="gsc_a_ac gs_ibl">5</span></td>
</tr>
</body></html>
"""


def test_parse_minimal_profile():
    data = parse_scholar_profile_html(SAMPLE_HTML)
    assert data.scholar_user_id == "TESTUSER1"
    assert data.name == "Autor Teste"
    assert data.affiliation == "UFMA"
    assert "Jornalismo" in data.interests
    assert data.metrics.citations_all == 42
    assert data.metrics.citations_since == 10
    assert data.metrics.h_index_all == 3
    assert data.metrics.since_year == 2020
    assert len(data.publications) == 1
    pub = data.publications[0]
    assert pub.title == "Artigo A"
    assert pub.authors == "A Silva"
    assert pub.year == 2019
    assert pub.citations == 5

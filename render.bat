REM asciidoctor --backend docbook -o out.xml "%~nx1" && pandoc --from docbook --to docx out.xml -o "%~n1.docx" --toc --toc-depth=3 --reference-doc=ref-Gyurmas.docx && asciidoctor-pdf -a pdf-theme=gy-theme.yml -a pdf-fontsdir=fonts "%~nx1" && "%~n1.pdf" && "%~n1.docx"
asciidoctor --backend docbook -o out.xml "%~nx1" && pandoc --from docbook --to docx out.xml -o "%~n1.docx" --toc --toc-depth=3 --reference-doc=ref-enGYneer.docx && asciidoctor-pdf -a pdf-theme=gy "%~nx1" && "%~n1.pdf" && "%~n1.docx"

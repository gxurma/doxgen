asciidoctor --backend docbook -o out.xml "%~nx1" && pandoc --from docbook --to docx out.xml -o "%~n1.docx" --toc --toc-depth=3 --reference-doc=ref-Gyurmas.docx && "%~n1.docx"

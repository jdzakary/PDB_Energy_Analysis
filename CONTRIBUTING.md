# Contributing to This Project

## Overview
The guidelines for code-style of specific languages are included below.
Additionally, please follow these miscellaneous guidelines:
* When adding a new page:
  * The function responsible for rendering the page should be called ```main```
  and should be located at the bottom of the file.
  * If possible, the main function should be kept short. It should serve as a
  logical control, making calls to other functions that do the heavy lifting.
  Here is a good example
  * ```python
    def main() -> None:
        st.title('Energy Heatmap')
        if check_files():
            if select_mode() == 'Side-by-Side':
                plot_side()
            else:
                plot_difference()
                view_difference()
        else:
            st.error('Not all Pre-Requisites are Calculated')
    
* When accessing a StringIO "File" stored in memory, always remember to
seek back to the start of the file using ```.seek(0)``` so the next call
to read the file is successful

## Python Code Style
* Follow PEP8 Guidelines when possible
* Type-Hinting
  * All function parameters should be type-hinted
  * All functions return values should be type-hinted
  * When accessing a variable whose type is not easily determined by an IDE,
    (Such as a variable in streamlit session state) type-hint the variable
* Function Docstrings
  * At the bare minimum, docstrings should have a concise title that
  accurately describes the purpose of the function
  * Ideally, function parameters should also be described in the docstring
  * Docstrings should use three double quotes ```"""```
  * The docstring title should be on a separate line from the opening double quotes
* Comments
  * No in-line comments
  * Avoid over commenting. Use comments to describe the general purpose of a code
  region, not what each code block is doing.
  * Keep comments to one line when possible. If the comment is longer than the
  PEP line length, then it is probably too long.
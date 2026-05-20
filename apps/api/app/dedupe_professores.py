"""Remove cadastros duplicados de professores. Execute: python -m app.dedupe_professores"""

import os
import sys

from sqlmodel import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from app.services.professor_dedupe import merge_duplicate_professors


def main():
    with Session(engine) as session:
        stats = merge_duplicate_professors(session)
        print(stats)


if __name__ == "__main__":
    main()

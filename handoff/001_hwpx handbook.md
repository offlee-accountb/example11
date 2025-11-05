pyhwpx 핵심 요약 핸드북
다음은 XML 직접 생성 방식에서 pyhwpx를 사용한 자동화로 마이그레이션하는 데 필요한 핵심 기능 요약입니다.
1. Document 생성 및 저장 방법
pyhwpx를 사용하면 한/글 프로그램을 실행하고 문서를 생성, 저장하는 과정을 간단하게 처리할 수 있습니다.
한/글 연결 및 새 문서 생성: Hwp() 클래스를 호출하면 한/글이 실행되어 있지 않으면 새 창을 생성하고, 실행 중이면 가장 최근에 활성화된 창에 연결합니다.[1][2]
문서 저장: save_as() 메서드를 사용하여 현재 문서를 지정된 경로와 파일명으로 저장할 수 있습니다. 경로에 폴더가 존재하지 않으면 자동으로 생성됩니다.
코드 예제:
code
Python
from pyhwpx import Hwp

# 한/글에 연결 (없으면 새로 실행)
hwp = Hwp()

# (문서 내용 작업)
hwp.insert_text("이것은 샘플 문서입니다.")

# 문서 저장 (다른 이름으로 저장)
hwp.save_as("C:\\temp\\결과물.hwp") 

# 한/글 종료
hwp.Quit()
2. Paragraph 추가 및 스타일 적용 방법
문서에 텍스트를 추가하고 문단 전체에 서식을 적용하는 방법입니다.
텍스트(문단) 추가: insert_text() 메서드를 사용하여 커서 위치에 문자열을 삽입합니다. 줄 바꿈이 필요할 경우 \r\n을 사용합니다.
스타일 적용: 텍스트를 삽입하기 전에 set_font() (글자 모양)나 ParaShape (문단 모양) 관련 메서드를 먼저 실행하면, 다음에 입력되는 내용에 해당 서식이 적용됩니다.
코드 예제:
code
Python
from pyhwpx import Hwp
hwp = Hwp()

# 문단 정렬 설정 (가운데 정렬)
hwp.ParagraphShapeAlignCenter()

# 글자 모양 설정 (돋움, 15pt, 굵게)
hwp.set_font(FaceName="돋움", Height=15, Bold=True)

# 텍스트 삽입
hwp.insert_text("제목: pyhwpx 핵심 기능 요약\r\n")

# 다음 문단을 위해 서식 초기화 (바탕글 스타일)
hwp.set_font(FaceName="바탕", Height=10, Bold=False)
hwp.ParagraphShapeAlignLeft()
hwp.insert_text("이 문서는 pyhwpx의 핵심 기능을 요약합니다.")
3. 인라인 텍스트 포맷팅 방법 (Run 단위 스타일 변경)
문단 내 특정 단어(Run)의 서식만 변경하려면 '선택 후 서식 변경' 방식을 사용합니다.
텍스트 선택: hwp.Move~ 계열의 다양한 커서 이동 명령어를 Select 모드나 MoveSel~ 명령어로 실행하여 원하는 텍스트 범위를 선택합니다.
서식 변경: 텍스트가 선택된 상태에서 set_font() 같은 서식 변경 메서드를 실행합니다.
코드 예제:
code
Python
from pyhwpx import Hwp
hwp = Hwp()

hwp.insert_text("pyhwpx를 사용하면 문서 자동화가 쉬워집니다.")

# 'pyhwpx' 단어만 찾아서 굵게, 파란색으로 변경
hwp.MoveDocBegin() # 문서 시작으로 이동
if hwp.find("pyhwpx"): # 'pyhwpx'를 찾아 선택
    hwp.set_font(Bold=True, TextColor="Blue")
hwp.Cancel() # 선택 해제
4. CharShape, ParaShape 설정 방법
set_font()와 같은 단축 메서드 외에, CharShape와 ParaShape 객체를 직접 조작하여 더 세밀한 서식 설정이 가능합니다.[3][4]
현재 커서 위치의 CharShape 또는 ParaShape 객체를 가져옵니다.
SetItem("속성이름", 값) 메서드로 원하는 속성을 변경합니다.
변경된 객체를 다시 할당하여 서식을 적용합니다.
주요 속성:
CharShape: Height(크기), Bold, Italic, FaceName(글꼴), TextColor(글자색), Spacing(자간)
ParaShape: AlignType(정렬), LineSpacing(줄 간격), PrevSpacing(문단 위 여백)
코드 예제:
code
Python
from pyhwpx import Hwp
hwp = Hwp()

hwp.MoveSelParaEnd() # 현재 문단 전체 선택

# CharShape으로 글자 속성 변경 (장평 95%, 기울임)
cs = hwp.CharShape
cs.SetItem("Ratio", 95)
cs.SetItem("Italic", True)
hwp.CharShape = cs

# ParaShape으로 문단 속성 변경 (오른쪽 정렬)
ps = hwp.ParaShape
ps.SetItem("AlignType", 2) # 0:양쪽, 1:왼쪽, 2:오른쪽, 3:가운데
hwp.ParaShape = ps

hwp.Cancel()
5. 멀티 폰트 지원 방법
문서 내에서 여러 종류의 한글 폰트를 사용하려면, 특정 텍스트를 선택하고 FaceName 속성을 변경해주면 됩니다. 이 방식은 인라인 텍스트 포맷팅(3번 항목)과 동일한 원리로 동작합니다.
코드 예제:
code
Python
from pyhwpx import Hwp
hwp = Hwp()

hwp.insert_text("기본 글꼴은 바탕체, 강조는 궁서체로 합니다.")

# '궁서체' 라는 단어를 찾아 실제 궁서 폰트로 변경
hwp.MoveDocBegin()
if hwp.find("궁서체"):
    hwp.set_font(FaceName="궁서")
hwp.Cancel()
6. 리스트(불릿, 번호) 처리 방법
제공된 핸드북 본문에는 프로그래밍 방식으로 글머리표(불릿)나 문단 번호 스타일을 직접 생성하거나 적용하는 방법에 대한 명시적인 설명이 포함되어 있지 않습니다. 이 기능은 스크립트 매크로 녹화를 통해 관련 액션(Action)과 파라미터를 확인한 후 저수준 API 호출 방식으로 구현해야 할 수 있습니다.
Sources
help
github.io
inflearn.com
inflearn.com
hancom.com
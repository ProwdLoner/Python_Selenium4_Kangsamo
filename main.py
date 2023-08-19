import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import pyperclip
import datetime
import json

# (프로그램 설정 변수)
# 네이버 아이디
config_naverId = "runitist"
config_naverPw = "todo"

config_ulTagIdListForTabList = [
    # 소형견
    'group157',
    # 중형견
    'group313',
    # 대형견
    'group187']

# 이어하기 설정
# ex :
# config_beforeClicked = {
#     '믹스견' : {
#         'min' : None,
#         'max' : None
#     },
# }
# 탭별, min 보다 작고, max 보다 큰 번호의 게시글만 탐색
# 둘다 None 혹은 탭 설정이 안되어 있다면 모두 탐색,
# min 만 None 이라면 max 보다 큰 번호의 게시글만 탐색 (더 큰 게시글이 없다면 바로 해당 탭 탐색 종료)
# max 만 None 이라면 min 보다 작은 번호의 게시글만 탐색 (더 작은 게시글이 나올 때까지 탐색 개시)
# 일단 해당 탭의 마지막 페이지, 마지막 게시글까지 탐지했다면, min 을 None 으로 두고, max 만 갱신해주기
config_beforeClicked = {
    '믹스견': {
        'max': None,
        'min': None
    },
}

# (프로그램 상태 변수)
# 학습 데이터 저장 파일
learningFile = None

needCreateNewFile = True

resultCount = 0


# (클래스)
# 댓글 정보 데이터 클래스
class Comment:
    def __init__(self, writerNickname, date, content, isReply, replyToNickname, includeImage):
        self.writerNickname = writerNickname
        self.date = date
        self.content = content
        self.isReply = isReply
        self.replyToNickname = replyToNickname
        self.includeImage = includeImage


# (알고리즘)
print("크롬 드라이버 생성")
options = Options()
options.add_argument("--disable-blink-features=AutomationControlled")
driver = webdriver.Chrome(options)

print("로그인 화면으로 이동")
driver.get("https://nid.naver.com/nidlogin.login")
WebDriverWait(driver, timeout=10).until(EC.presence_of_element_located(
    (By.ID, 'id')))
WebDriverWait(driver, timeout=10).until(EC.presence_of_element_located(
    (By.ID, 'pw')))

naverIdElem = driver.find_element(By.ID, 'id')
naverIdElem.click()
pyperclip.copy(config_naverId)
naverIdElem.send_keys(Keys.CONTROL, 'v')
time.sleep(0.1)

naverPwElem = driver.find_element(By.ID, 'pw')
naverPwElem.click()
pyperclip.copy(config_naverPw)
naverPwElem.send_keys(Keys.CONTROL, 'v')
time.sleep(0.1)

WebDriverWait(driver, timeout=10).until(EC.presence_of_element_located(
    (By.ID, 'log.login')))
driver.find_element(By.ID, 'log.login').click()

isLogin = False
print("로그인 완료까지 대기 중")
while not isLogin:
    time.sleep(1)
    isLogin = driver.current_url == "https://www.naver.com/"

print("로그인 완료 = 브라우저가 인증 세션을 취득함")

print("강사모 게시판 이동")
driver.get("https://cafe.naver.com/dogpalza")

print("탭 리스트 컨테이너 순회 시작")
completeTabList = []
for config_ulTagIdForTabList in config_ulTagIdListForTabList:
    print("%s 탭 리스트 순회 시작" % config_ulTagIdForTabList)

    speciesText = ""
    if config_ulTagIdForTabList == "group157":
        speciesText = "소형견"
    elif config_ulTagIdForTabList == "group313":
        speciesText = "중형견"
    elif config_ulTagIdForTabList == "group187":
        speciesText = "대형견"

    tabListLoop = True
    while tabListLoop:
        # ul 태그 객체 가져오기
        WebDriverWait(driver, timeout=10).until(EC.presence_of_element_located((By.ID, config_ulTagIdForTabList)))
        config_ulTagObjectForTabList = driver.find_element(By.ID, config_ulTagIdForTabList)
        # ul 태그 객체 내의 li 태그들 가져오기
        config_ulTagLiTagObjectListForTabList = config_ulTagObjectForTabList.find_elements(By.TAG_NAME, 'li')

        tabListLoop = False
        for config_ulTagLiTagObjectForTabList in config_ulTagLiTagObjectListForTabList:
            tabText = config_ulTagLiTagObjectForTabList.text
            if not completeTabList.__contains__(tabText):
                tabListLoop = True
                completeTabList.append(tabText)

                # li 태그 내 a 태그 가져오기
                WebDriverWait(config_ulTagLiTagObjectForTabList, timeout=10).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'a')))
                config_ulTagLiTagATagObjectForTabList = config_ulTagLiTagObjectForTabList.find_element(By.TAG_NAME, 'a')
                print("%s 탭으로 이동" % tabText)
                config_ulTagLiTagATagObjectForTabList.click()

                # driver 를 iframe 영역으로 스위칭
                WebDriverWait(driver, timeout=10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="cafe_main"]')))
                driver.switch_to.frame(driver.find_element(By.XPATH, '//*[@id="cafe_main"]'))

                # 한 페이지당 50개씩 보기
                WebDriverWait(driver, timeout=10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="listSizeSelectDiv"]/a')))
                driver.find_element(By.XPATH, '//*[@id="listSizeSelectDiv"]/a').click()
                WebDriverWait(driver, timeout=10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="listSizeSelectDiv"]/ul/li[7]/a')))
                driver.find_element(By.XPATH, '//*[@id="listSizeSelectDiv"]/ul/li[7]/a').click()

                print("%s 탭의 페이지 리스트 순회 시작" % tabText)
                beforePageIdx = 0
                needPageLoopBreak = False
                while True:
                    # 페이지 리스트 컨테이너 객체
                    WebDriverWait(driver, timeout=10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'prev-next')))
                    pageListContainerObj = driver.find_element(By.CLASS_NAME, 'prev-next')

                    # 마지막 페이지 객체
                    pageBtnObjList = pageListContainerObj.find_elements(By.TAG_NAME, 'a')
                    lastPageObj = pageBtnObjList[len(pageBtnObjList) - 1]
                    lastPageBtnText = lastPageObj.text.replace(',', '')

                    # 현재 선택된 페이지 객체
                    WebDriverWait(pageListContainerObj, timeout=10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'a.on')))
                    currentPageBtnObj = pageListContainerObj.find_element(By.CSS_SELECTOR, 'a.on')
                    currentPageBtnText = currentPageBtnObj.text.replace(',', '')
                    currentPageBtnIdx = int(currentPageBtnText)

                    print("%s 탭의 %s 페이지" % (tabText, currentPageBtnText))

                    if currentPageBtnIdx <= beforePageIdx:
                        # 현재 처리할 페이지 번호가 전에 처리한 페이지 번호보다 작거나 같을 때(= 순환 되었을 때),
                        # 페이지 순회 루프 탈출
                        print("이전 %d 페이지, 현재 %d 페이지 -> 페이지 순환" % (beforePageIdx, currentPageBtnIdx))
                        break

                    if lastPageBtnText == currentPageBtnText:
                        # 현재 페이지가 곧 마지막 페이지
                        # 현 페이지 작업이 끝난 후 break
                        needPageLoopBreak = True

                    print("%s 탭의 %s 페이지 게시글 리스트 순회 시작" % (tabText, currentPageBtnText))
                    beforeArticleUid = None
                    articleListLoop = True
                    while articleListLoop:
                        # 게시글 리스트 가져오기
                        articles = driver.find_elements(By.XPATH, '//*[@id="main-area"]/div[5]/table/tbody/tr')

                        articleListLoop = False
                        for article in articles:
                            # 게시글 리스트 아이템 정보 가져오기
                            WebDriverWait(article, timeout=10).until(
                                EC.presence_of_element_located((By.CLASS_NAME, 'td_article')))
                            articleBoxObj = article.find_element(By.CLASS_NAME, 'td_article')

                            # 게시글 일련번호 (일련번호는 탐색을 진행할수록 작아짐)
                            WebDriverWait(articleBoxObj, timeout=10).until(
                                EC.presence_of_element_located((By.CLASS_NAME, 'board-number')))
                            articleBoardNumber = articleBoxObj.find_element(By.CLASS_NAME, 'board-number')
                            WebDriverWait(articleBoardNumber, timeout=10).until(
                                EC.presence_of_element_located((By.CLASS_NAME, 'inner_number')))
                            articleInnerNumberText = articleBoardNumber.find_element(By.CLASS_NAME, 'inner_number').text
                            boardNumberInt = int(articleInnerNumberText)

                            if beforeArticleUid is None or beforeArticleUid > boardNumberInt:
                                # 이전 처리된 uid 가 없거나, 혹은 이전 처리 uid 보다 작은 경우

                                # 설정에 따른 게시글 스킵 여부 확인
                                if tabText in config_beforeClicked:
                                    tabClicked = config_beforeClicked[tabText]
                                    clickedMax = tabClicked["max"]
                                    clickedMin = tabClicked["min"]

                                    if (clickedMax is not None and
                                            clickedMin is not None):
                                        # 최대 일련번호 설정과 최소 일련번호 설정이 모두 None 이 아닐 경우
                                        if clickedMax >= boardNumberInt >= clickedMin:
                                            # 현재 일련번호가 최대 일련번호 설정보다 이하면서, 최소 일련번호 설정 이상
                                            print("현재 일련번호(" +
                                                  str(boardNumberInt) +
                                                  ")가 최대 일련번호 설정(" +
                                                  str(clickedMax) +
                                                  ") 이하면서, 최소 일련번호 설정(" +
                                                  str(clickedMin) +
                                                  ") 이상입니다. -> 스킵")
                                            continue
                                    else:
                                        # 최대 일련번호 설정과 최소 일련번호 설정 중 None 이 하나라도 있는 경우
                                        if clickedMin is not None and \
                                                clickedMin <= boardNumberInt:
                                            # 최소 일련번호 설정이 not None 이면서,
                                            # 현재 일련번호가 최소 일련번호 설정 이상
                                            print("현재 일련번호(" +
                                                  str(boardNumberInt) +
                                                  ")가 최소 일련번호 설정(" +
                                                  str(clickedMin) +
                                                  ") 이상입니다. -> 스킵")
                                            continue
                                        elif clickedMax is not None and \
                                                clickedMax >= boardNumberInt:
                                            # 최대 일련번호 설정이 not None 이면서,
                                            # 현재 일련번호가 최대 일련번호 설정 이하
                                            print("현재 일련번호(" +
                                                  str(boardNumberInt) +
                                                  ")가 최대 일련번호 설정(" +
                                                  str(clickedMax) +
                                                  ") 이하입니다. -> 탐색 종료")
                                            needPageLoopBreak = True
                                            break

                                # 게시글 A태그 (+ 타이틀)
                                WebDriverWait(articleBoxObj, timeout=10).until(
                                    EC.presence_of_element_located((By.CLASS_NAME, 'board-list')))
                                boardList = articleBoxObj.find_element(By.CLASS_NAME, 'board-list')

                                WebDriverWait(boardList, timeout=10).until(
                                    EC.presence_of_element_located((By.CLASS_NAME, 'inner_list')))
                                innerList = boardList.find_element(By.CLASS_NAME, 'inner_list')

                                WebDriverWait(innerList, timeout=10).until(
                                    EC.presence_of_element_located((By.CLASS_NAME, 'article')))
                                boardAtagObj = innerList.find_element(By.CLASS_NAME, 'article')

                                # 게시글 타이틀
                                boardTitleText = boardAtagObj.text

                                # 게시글 작성자 이름
                                WebDriverWait(article, timeout=10).until(
                                    EC.presence_of_element_located((By.CLASS_NAME, 'td_name')))
                                tdName = article.find_element(By.CLASS_NAME, 'td_name')

                                WebDriverWait(tdName, timeout=10).until(
                                    EC.presence_of_element_located((By.CLASS_NAME, 'm-tcol-c')))
                                mtcolc = tdName.find_element(By.CLASS_NAME, 'm-tcol-c')

                                nickNameText = mtcolc.text

                                # 게시글 작성일(15:43 or 2023.07.22.)
                                WebDriverWait(article, timeout=10).until(
                                    EC.presence_of_element_located((By.CLASS_NAME, 'td_date')))
                                tdDate = article.find_element(By.CLASS_NAME, 'td_date')

                                dateText = tdDate.text

                                # 게시글 방문 회수
                                WebDriverWait(article, timeout=10).until(
                                    EC.presence_of_element_located((By.CLASS_NAME, 'td_view')))
                                tdView = article.find_element(By.CLASS_NAME, 'td_view')

                                viewText = tdView.text

                                # 게시글 좋아요 개수
                                WebDriverWait(article, timeout=10).until(
                                    EC.presence_of_element_located((By.CLASS_NAME, 'td_likes')))
                                tdLikes = article.find_element(By.CLASS_NAME, 'td_likes')

                                likeText = tdLikes.text

                                print(
                                    "%s 탭의 %s UID 게시글\ntitle : %s, nickname : %s, date : %s, view : %s, like : %s" % (
                                        tabText, articleInnerNumberText, boardTitleText, nickNameText, dateText,
                                        viewText,
                                        likeText))

                                print("게시글 상세 페이지로 이동")
                                boardAtagObj.click()

                                # 게시글 내용 위치 iframe 으로 이동
                                driver.switch_to.default_content()
                                WebDriverWait(driver, timeout=10).until(
                                    EC.presence_of_element_located((By.XPATH, '//*[@id="cafe_main"]')))
                                driver.switch_to.frame(driver.find_element(By.XPATH, '//*[@id="cafe_main"]'))

                                print("게시글 내용 파악")
                                # 게시글 타이틀
                                WebDriverWait(driver, timeout=10).until(EC.presence_of_element_located(
                                    (By.CSS_SELECTOR,
                                     'div.ArticleContentBox>.article_header>.ArticleTitle>.title_area>.title_text')))
                                titleText = driver.find_element(
                                    By.CSS_SELECTOR,
                                    'div.ArticleContentBox>.article_header>.ArticleTitle>.title_area>.title_text').text

                                # 게시글 본문 컨테이너
                                WebDriverWait(driver, timeout=10).until(EC.presence_of_element_located(
                                    (By.CLASS_NAME, 'article_viewer')))
                                articleViewer = driver.find_element(
                                    By.CLASS_NAME, 'article_viewer')

                                contentContainerObjects = articleViewer.find_elements(
                                    By.CSS_SELECTOR, 'div.se-component')

                                contentText = ""

                                # 게시글 내용에 이미지 혹은 다른 리소스가 포함되어있는지
                                includeImage = False
                                includeEtc = False

                                print("게시글 본문 파악 및 합성")
                                for contentContainer in contentContainerObjects:
                                    # 문장 이어붙이기시 문장별 Split 결정
                                    if contentText == "":
                                        appendString = ""
                                    else:
                                        appendString = " "

                                    if "se-text" in contentContainer.get_attribute("class"):
                                        # 타입이 텍스트
                                        contentText += appendString + contentContainer.text
                                    elif "se-image" in contentContainer.get_attribute(
                                            "class") or "se-sticker" in contentContainer.get_attribute("class"):
                                        if len(contentContainer.find_elements(By.TAG_NAME, "img")) == 0:
                                            continue

                                        # 타입이 이미지(%< >% 안에 이미지 링크 넣기)
                                        contentText += appendString + "%<" + contentContainer.find_element(By.TAG_NAME,
                                                                                                           "img").get_attribute(
                                            "src") + ">%"
                                        includeImage = True
                                    else:
                                        # 타입이 그외
                                        # todo 다른 리소스도 추출 가능하도록 고도화
                                        # contentText += appendString + contentContainer.get_attribute('outerHTML')
                                        includeEtc = True

                                # !!!타이틀, 본문 내용을 기반으로 필터링!!
                                # --------------------------------------------------------------
                                # 스킵 여부 확인
                                if includeEtc:
                                    # 텍스트가 아니고, 이미지도 아닐때 스킵
                                    print("게시글이 텍스트 or 이미지가 아님 -> 스킵")
                                    print("게시글에서 복귀")
                                    driver.back()

                                    # iframe 으로 이동
                                    driver.switch_to.default_content()
                                    WebDriverWait(driver, timeout=10).until(EC.presence_of_element_located(
                                        (By.XPATH, '//*[@id="cafe_main"]')))
                                    driver.switch_to.frame(driver.find_element(By.XPATH, '//*[@id="cafe_main"]'))

                                    articleListLoop = True
                                    beforeArticleUid = boardNumberInt
                                    break
                                # --------------------------------------------------------------

                                print("게시글 내용 추출\ntitle : %s, content : %s, includeImage : %r, includeEtc : %r" % (
                                    titleText, contentText, includeImage, includeEtc))

                                print("댓글 리스트 순회")
                                commentList = []
                                if len(driver.find_elements(By.CSS_SELECTOR, 'ul.comment_list')) != 0:
                                    WebDriverWait(driver, timeout=10).until(EC.presence_of_element_located(
                                        (By.CSS_SELECTOR, 'ul.comment_list')))
                                    ulCommentList = driver.find_element(By.CSS_SELECTOR,
                                                                        'ul.comment_list')

                                    commentObjects = ulCommentList.find_elements(By.TAG_NAME, "li")

                                    for commentObject in commentObjects:
                                        # Comment 면 False, Reply 면 True
                                        isReply = "CommentItem--reply" in commentObject.get_attribute("class")

                                        commentBoxItems = commentObject.find_elements(By.CSS_SELECTOR,
                                                                                      'div.comment_box>div')

                                        # 댓글 작성자 닉네임
                                        commentWriterNick = ""
                                        # 댓글 작성일
                                        commentDate = ""
                                        # 댓글 본문
                                        commentContent = ""
                                        # 대댓글 대상자 닉네임
                                        replyToNickname = None

                                        commentIncludeImage = False

                                        # 댓글 컨테이너 내 요소 순회
                                        for commentBoxItem in commentBoxItems:
                                            if commentContent == "":
                                                appendString = ""
                                            else:
                                                appendString = " "

                                            if "comment_nick_box" in commentBoxItem.get_attribute("class"):
                                                # 타입이 닉네임
                                                commentWriterNick = commentBoxItem.text
                                            elif "comment_info_box" in commentBoxItem.get_attribute("class"):
                                                # 타입이 정보
                                                WebDriverWait(commentBoxItem, timeout=10).until(
                                                    EC.presence_of_element_located(
                                                        (By.CLASS_NAME, 'comment_info_date')))
                                                commentDate = commentBoxItem.find_element(By.CLASS_NAME,
                                                                                          'comment_info_date').text
                                            elif "comment_text_box" in commentBoxItem.get_attribute("class"):
                                                # 타입이 텍스트
                                                if isReply:
                                                    findReplyTo = commentBoxItem.find_elements(By.CSS_SELECTOR,
                                                                                               'p.comment_text_view>a')
                                                    if len(findReplyTo) != 0:
                                                        replyToNickname = findReplyTo[0].text

                                                    WebDriverWait(commentBoxItem, timeout=10).until(
                                                        EC.presence_of_element_located(
                                                            (By.CSS_SELECTOR, 'p.comment_text_view>span.text_comment')))
                                                    commentContent += appendString + commentBoxItem.find_element(
                                                        By.CSS_SELECTOR,
                                                        'p.comment_text_view>span.text_comment').text
                                                else:
                                                    commentContent += appendString + commentBoxItem.text

                                            elif "CommentItemImage" in commentBoxItem.get_attribute(
                                                    "class") or "CommentItemSticker" in commentBoxItem.get_attribute(
                                                "class"):
                                                if len(commentBoxItem.find_elements(By.TAG_NAME, "img")) == 0:
                                                    continue

                                                # 타입이 이미지
                                                WebDriverWait(commentBoxItem, timeout=10).until(
                                                    EC.presence_of_element_located(
                                                        (By.TAG_NAME, 'img')))
                                                commentContent += appendString + str(
                                                    commentBoxItem.find_element(By.TAG_NAME, "img").get_attribute(
                                                        "src"))
                                                commentIncludeImage = True
                                            elif "comment_tool" in commentBoxItem.get_attribute("class"):
                                                # 타입이 그외
                                                continue

                                        # !!!댓글 정보를 기반으로 필터링!!

                                        # 댓글 정보를 리스트에 추가
                                        print(
                                            "댓글 정보 수집\ncommentWriterNick : %s, commentDate : %s, commentContent : %s, isReply : %r, replyToNickname : %s, commentIncludeImage : %r" % (
                                                commentWriterNick, commentDate, commentContent, isReply,
                                                replyToNickname,
                                                commentIncludeImage))

                                        commentList.append(
                                            Comment(commentWriterNick, commentDate, commentContent, isReply,
                                                    replyToNickname, commentIncludeImage))

                                for commentObj in commentList:
                                    nowDateText = ''

                                    if ':' in dateText:
                                        nowDateText = datetime.datetime.now().strftime("%Y.%m.%d.")
                                    else:
                                        nowDateText = dateText

                                    learningData = {"articleNumber": boardNumberInt,
                                                    "articleCreateDate": nowDateText,
                                                    "articleWriterNickname": nickNameText,
                                                    "articleViewCount": viewText,
                                                    "articleLikeCount": likeText,
                                                    "articleTitle": titleText,
                                                    "articleContent": contentText,
                                                    "articleIncludeImage": includeImage,
                                                    "commentWriterNick": commentObj.writerNickname,
                                                    "commentCreateDate": commentObj.date,
                                                    "commentContent": commentObj.content,
                                                    "commentIsReply": commentObj.isReply,
                                                    "commentReplyToNickname": commentObj.replyToNickname,
                                                    "commentIncludeImage": commentObj.includeImage}

                                    jsonString = json.dumps(learningData, ensure_ascii=False) + '\n'
                                    print("jsonString : %s" % jsonString)

                                    if needCreateNewFile:
                                        fileName = speciesText + "_" + tabText + "_" + "learning_data_" + (
                                            datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")) + ".jsonl"

                                        print("createNewFile : %s" % fileName)

                                        learningFile = open(fileName, 'w', encoding="utf-8")
                                        needCreateNewFile = False

                                    learningFile.write(jsonString)
                                    resultCount += 1
                                    print("write jsonString to File %d" % resultCount)

                                    if resultCount == 1000:
                                        print("1000 Collect!!!")

                                        needCreateNewFile = True
                                        resultCount = 0

                                print("게시글에서 복귀")
                                driver.back()

                                # iframe 으로 이동
                                driver.switch_to.default_content()
                                WebDriverWait(driver, timeout=10).until(EC.presence_of_element_located(
                                    (By.XPATH, '//*[@id="cafe_main"]')))
                                driver.switch_to.frame(driver.find_element(By.XPATH, '//*[@id="cafe_main"]'))

                                articleListLoop = True
                                beforeArticleUid = boardNumberInt
                                break

                    if needPageLoopBreak:
                        print("마지막 페이지 처리 완료")
                        break

                        # 처리된 페이지 인덱스 정보 갱신
                    beforePageIdx = currentPageBtnIdx

                    # 다음 페이지로 이동
                    # 페이지 리스트 컨테이너 객체
                    WebDriverWait(driver, timeout=10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'prev-next')))
                    pageListContainerObjForNext = driver.find_element(By.CLASS_NAME, 'prev-next')

                    # 현재 선택된 페이지 객체
                    currentPageBtnObjListForNext = pageListContainerObjForNext.find_elements(By.TAG_NAME, 'a')

                    for idx in range(len(currentPageBtnObjListForNext)):
                        # 선택된 페이지 버튼이 나올 때까지 순회
                        page = currentPageBtnObjListForNext[idx]
                        pageText = page.text.replace(',', '')
                        pageIsSelected = page.get_attribute("class") == "on"

                        if pageIsSelected:
                            currentPageBtnObjListForNext[idx + 1].click()
                            break

                print("탭 선택으로 복귀")
                driver.back()

if learningFile is not None:
    learningFile.close()

print("완료 - 크롬 드라이버 종료")
driver.close()

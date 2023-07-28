from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os as os

# 파이썬 Selenium 4 웹 스크래퍼
# 네이버 블로그 강사모를 타겟으로 GPT-3 학습용 데이터 스크래핑

# 팁 :
# 1. 요소가 없다는 에러가 나온다면,
#     WebDriverWait(driver, timeout=10).until(EC.presence_of_element_located((By.XPATH, '대기할 요소의 XPATH')))
#     를 앞에 사용해보기
# 2. 게시글은 페이지 1의 상위부터 순차로 탐색합니다. 게시글 일련번호는 큰 숫자에서 작은 숫자로 이어집니다.

# 주의사항 :
# 1. 강사모 카페글은 페이지 순환 가능성이 있습니다. 예를들면 1000 페이지에서 다음을 누르면 다시 1 페이지로 복귀합니다. 이에 대한 처리가 되어있습니다.
# 2. 별다른 필터링 없이 정보를 저장하는 것만으로 게시물 10 개를 긁어오는데 평균 30초 정도가 소모됩니다. 이어받기 기능이 준비되어있습니다.

# (프로그램 설정)
# 네이버 아이디
config_naverId = "runitist"

# 스크래핑 할 게시글 리스트 버튼의 XPath
config_postXpath = '//*[@id="menuLink174"]'

# 이 번호보다 큰 번호의 게시글을 탐색 (ex : None or 18147868)
config_beforeClickedArticleNumberMax = None

# 이 번호보다 작은 번호의 게시글을 탐색 (ex : None or 18144769)
config_beforeClickedArticleNumberMin = None


# (클래스)
# 댓글 정보 데이터 클래스
class Comment:
    def __init__(self, writerNickname, date, content, isReply, replyToNickname):
        self.writerNickname = writerNickname
        self.date = date
        self.content = content
        self.isReply = isReply
        self.replyToNickname = replyToNickname


# (알고리즘)
print("크롬 드라이버 생성")
driver = webdriver.Chrome()

print("로그인 화면으로 이동")
driver.get("https://nid.naver.com/nidlogin.login")
driver.find_element(By.ID, 'id').send_keys(config_naverId)
driver.find_element(By.ID, 'pw').send_keys("empty")
driver.find_element(By.ID, 'log.login').click()

isLogin = False
print("로그인 완료까지 대기 중")
while not isLogin:
    time.sleep(1)
    isLogin = driver.current_url == "https://www.naver.com/"

# 로그인 완료 = 브라우저가 인증 세션을 취득함

print("강사모 게시판 이동")
driver.get("https://cafe.naver.com/dogpalza")

print("설정한 게시글 타입으로 이동")
driver.find_element(By.XPATH, config_postXpath).click()

# iframe 영역을 조작하기 위한 스위칭 (되돌아오려면 driver.switch_to.default_content())
print("iframe 영역으로 스위칭")
driver.switch_to.frame(driver.find_element(By.XPATH, '//*[@id="cafe_main"]'))

print("한 페이지당 50개씩 보기")
driver.find_element(By.XPATH, '//*[@id="listSizeSelectDiv"]/a').click()
driver.find_element(By.XPATH, '//*[@id="listSizeSelectDiv"]/ul/li[7]/a').click()

# 프로그램 시작 후 처음 방문한 게시글 일련번호(= 현 시점 탐색한 가장 큰 일련번호)
maxClickedArticleNumber = None

# 이 번호보다 작은 번호의 게시글을 탐색
beforeClickedArticleNumberMin = None

# 페이지를 전부 순회할 때까지 루프
pageLoop = True
while pageLoop:
    print("공지를 제외한 게시글 리스트 가져오기")
    articleLoop = True
    while articleLoop:
        # 게시글 Row 리스트 가져오기
        articles = driver.find_elements(By.XPATH, '//*[@id="main-area"]/div[5]/table/tbody/tr')

        articleLoop = False
        for article in articles:
            # 게시글 Row 정보 가져오기
            articleBoxObj = article.find_element(By.CLASS_NAME, 'td_article')

            # 게시글 일련번호 (일련번호는 탐색을 진행할수록 작아짐)
            boardNumber = int((articleBoxObj.find_element(By.CLASS_NAME, 'board-number')
                               .find_element(By.CLASS_NAME, 'inner_number').text))

            if beforeClickedArticleNumberMin is None or beforeClickedArticleNumberMin > boardNumber:
                # 기존에 방문한 게시글 일련번호가 비교 대상 게시글 일련번호보다 클 경우

                print("게시글 일련번호 스킵 설정 판별")
                if (config_beforeClickedArticleNumberMax is not None and
                        config_beforeClickedArticleNumberMin is not None):
                    # 최대 일련번호 설정과 최소 일련번호 설정이 모두 None 이 아닐 경우
                    if config_beforeClickedArticleNumberMax >= boardNumber >= config_beforeClickedArticleNumberMin:
                        # 현재 일련번호가 최대 일련번호 설정보다 이하면서, 최소 일련번호 설정 이상
                        print("현재 일련번호(" +
                              str(boardNumber) +
                              ")가 최대 일련번호 설정(" +
                              str(config_beforeClickedArticleNumberMax) +
                              ") 이하면서, 최소 일련번호 설정(" +
                              str(config_beforeClickedArticleNumberMin) +
                              ") 이상입니다. -> 스킵")
                        continue
                else:
                    # 최대 일련번호 설정과 최소 일련번호 설정 중 None 이 하나라도 있는 경우
                    if config_beforeClickedArticleNumberMin is not None and \
                            config_beforeClickedArticleNumberMin <= boardNumber:
                        # 최소 일련번호 설정이 not None 이면서,
                        # 현재 일련번호가 최소 일련번호 설정 이상
                        print("현재 일련번호(" +
                              str(boardNumber) +
                              ")가 최소 일련번호 설정(" +
                              str(config_beforeClickedArticleNumberMin) +
                              ") 이상입니다. -> 스킵")
                        continue
                    elif config_beforeClickedArticleNumberMax is not None and \
                            config_beforeClickedArticleNumberMax >= boardNumber:
                        # 최대 일련번호 설정이 not None 이면서,
                        # 현재 일련번호가 최대 일련번호 설정 이하
                        print("현재 일련번호(" +
                              str(boardNumber) +
                              ")가 최대 일련번호 설정(" +
                              str(config_beforeClickedArticleNumberMax) +
                              ") 이하입니다. -> 탐색 종료")
                        pageLoop = False
                        break

                print("게시글 리스트 아이템 정보 가져오기")
                # 게시글 A태그 (+ 타이틀)
                boardAtagObj = (articleBoxObj.find_element(By.CLASS_NAME, 'board-list')
                                .find_element(By.CLASS_NAME, 'inner_list')
                                .find_element(By.CLASS_NAME, 'article'))

                # 게시글 작성자 이름
                nickNameText = article.find_element(By.CLASS_NAME, 'td_name').find_element(By.CLASS_NAME,
                                                                                           'm-tcol-c').text

                # 게시글 작성일(15:43 or 2023.07.22.)
                dateText = article.find_element(By.CLASS_NAME, 'td_date').text

                # 게시글 방문 회수
                viewText = article.find_element(By.CLASS_NAME, 'td_view').text

                # 게시글 좋아요 개수
                likeText = article.find_element(By.CLASS_NAME, 'td_likes').text

                # !!!게시글 리스트 아이템 정보를 가지고 필터링 -> 스킵이 필요하면 continue!!

                print("게시글(" + str(boardNumber) + ")로 이동")
                boardAtagObj.click()

                # 게시글 내용 위치로 이동
                driver.switch_to.default_content()
                driver.switch_to.frame(driver.find_element(By.XPATH, '//*[@id="cafe_main"]'))

                print("게시글 내용 추출")
                # 게시글 타이틀
                WebDriverWait(driver, timeout=10).until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'div.ArticleContentBox>.article_header>.ArticleTitle>.title_area>.title_text')))
                titleText = driver.find_element(
                    By.CSS_SELECTOR, 'div.ArticleContentBox>.article_header>.ArticleTitle>.title_area>.title_text').text

                # 게시글 본문 컨테이너
                WebDriverWait(driver, timeout=10).until(EC.presence_of_element_located(
                    (By.CLASS_NAME, 'article_viewer')))
                contentContainerObjects = driver.find_element(
                    By.CLASS_NAME, 'article_viewer').find_elements(
                    By.CSS_SELECTOR, 'div.se-component')

                contentText = ""

                for contentContainer in contentContainerObjects:
                    if contentText == "":
                        appendString = ""
                    else:
                        appendString = " "

                    if "se-text" in contentContainer.get_attribute("class"):
                        # 타입이 텍스트
                        contentText += appendString + contentContainer.text
                    elif "se-image" in contentContainer.get_attribute(
                            "class") or "se-sticker" in contentContainer.get_attribute("class"):
                        # 타입이 이미지
                        contentText += appendString + contentContainer.find_element(By.TAG_NAME, "img").get_attribute(
                            "src")
                    else:
                        # 타입이 그외
                        contentText += appendString + contentContainer.get_attribute('outerHTML')
                    # todo se-video 영상 주소 추출 등 고도화

                # !!!타이틀, 본문 내용을 기반으로 필터링!!

                print("댓글 내용 추출")
                commentList = []
                if len(driver.find_elements(By.CSS_SELECTOR, 'ul.comment_list')) != 0:
                    commentObjects = driver.find_element(By.CSS_SELECTOR, 'ul.comment_list').find_elements(By.TAG_NAME,
                                                                                                           "li")
                    for commentObject in commentObjects:
                        # Comment 면 False, Reply 면 True
                        isReply = "CommentItem--reply" in commentObject.get_attribute("class")

                        commentBoxItems = commentObject.find_elements(By.CSS_SELECTOR, 'div.comment_box>div')

                        # 댓글 작성자 닉네임
                        commentWriterNick = ""
                        # 댓글 작성일
                        commentDate = ""
                        # 댓글 본문
                        commentContent = ""
                        # 대댓글 대상자 닉네임
                        replyToNickname = None

                        # 댓글 컨테이너 내 요소 순회
                        for commentBoxItem in commentBoxItems:
                            if contentText == "":
                                appendString = ""
                            else:
                                appendString = " "

                            if "comment_nick_box" in commentBoxItem.get_attribute("class"):
                                # 타입이 닉네임
                                commentWriterNick = commentBoxItem.text
                            elif "comment_info_box" in commentBoxItem.get_attribute("class"):
                                # 타입이 정보
                                commentDate = commentBoxItem.find_element(By.CLASS_NAME, 'comment_info_date').text
                            elif "comment_text_box" in commentBoxItem.get_attribute("class"):
                                # 타입이 텍스트
                                if isReply:
                                    findReplyTo = commentBoxItem.find_elements(By.CSS_SELECTOR, 'p.comment_text_view>a')
                                    if len(findReplyTo) != 0:
                                        replyToNickname = findReplyTo[0].text
                                    commentContent += appendString + commentBoxItem.find_element(By.CSS_SELECTOR,
                                                                                                 'p.comment_text_view>span.text_comment').text
                                else:
                                    commentContent += appendString + commentBoxItem.text

                            elif "CommentItemImage" in commentBoxItem.get_attribute(
                                    "class") or "CommentItemSticker" in commentBoxItem.get_attribute("class"):
                                # 타입이 이미지
                                commentContent += appendString + str(
                                    commentBoxItem.find_element(By.TAG_NAME, "img").get_attribute(
                                        "src"))
                            elif "comment_tool" in commentBoxItem.get_attribute("class"):
                                # 타입이 그외
                                continue
                            else:
                                commentContent += appendString + commentBoxItem.get_attribute('outerHTML')

                        # !!!댓글 정보를 기반으로 필터링!!

                        # 댓글 정보를 리스트에 추가
                        commentList.append(
                            Comment(commentWriterNick, commentDate, commentContent, isReply, replyToNickname))

                print("\n------------------")
                print(nickNameText)
                print(dateText)
                print(viewText)
                print(likeText)
                print(titleText)
                print(contentText)
                for commentobj in commentList:
                    print(commentobj.isReply)
                    print(commentobj.replyToNickname)
                    print(commentobj.writerNickname)
                    print(commentobj.date)
                    print(commentobj.content)
                print("------------------\n")
                # todo 정보(nickNameText, dateText, viewText, likeText, titleText, contentText, commentList)를 파일로 저장

                if maxClickedArticleNumber is None:
                    # 아직 게시글 분석을 한번도 한 적이 없음
                    maxClickedArticleNumber = boardNumber
                    # 파일에 Max Index 저장하기
                    if os.path.isfile("min_max_board_number.txt"):
                        os.remove("min_max_board_number.txt")
                    f = open("min_max_board_number.txt", 'w')
                    f.write('{"MaxBoardNumber" : ' + str(maxClickedArticleNumber) + ', "minBoardNumber" : ' + str(
                        maxClickedArticleNumber) + '}')
                    f.close()
                else:
                    # 게시글 분석을 한 적이 있음
                    # 파일에 Min Index 저장하기
                    if os.path.isfile("min_max_board_number.txt"):
                        os.remove("min_max_board_number.txt")
                    f = open("min_max_board_number.txt", 'w')
                    f.write('{"MaxBoardNumber" : ' + str(maxClickedArticleNumber) + ', "minBoardNumber" : ' + str(
                        boardNumber) + '}')
                    f.close()

                print("게시글에서 복귀")
                driver.back()

                # iframe 영역을 조작하기 위한 스위칭 (되돌아오려면 driver.switch_to.default_content())
                print("iframe 영역으로 스위칭")
                driver.switch_to.frame(driver.find_element(By.XPATH, '//*[@id="cafe_main"]'))

                # 데이터 갱신
                beforeClickedArticleNumberMin = boardNumber
                articleLoop = True
                break

    # 아래로는 다음 페이지로 이동, 혹은 탐색 루프 탈출 로직
    print("게시판 페이지 버튼 리스트 가져오기")
    pageList = driver.find_element(By.CLASS_NAME, 'prev-next').find_elements(By.TAG_NAME, "a")

    print("다음 페이지 버튼 조회")
    for idx in range(len(pageList)):
        # 선택된 페이지 버튼이 나올 때까지 순회
        page = pageList[idx]
        pageIsSelected = page.get_attribute("class") == "on"
        pageText = page.text.replace(',', '')
        print("페이지 번호 : " + pageText + ", 선택여부 : " + str(pageIsSelected))

        if pageIsSelected:
            # 선택된 페이지 버튼 발견
            if idx == len(pageList) - 1:
                # 현재 선택된 버튼이 마지막 버튼일 때 -> 루프 빠져나오기
                pageLoop = False
                print("마지막 페이지 -> 페이지 탐색 루프 탈출")
                break
            else:
                # 선택된 페이지 번호 다음 번호를 클릭
                print("선택된 페이지 번호(" +
                      pageText +
                      ") 다음 버튼(" +
                      pageList[idx + 1].text.replace(',', '') +
                      ")을 클릭")
                pageList[idx + 1].click()

                print("새로운 게시판 페이지 버튼 리스트 가져오기")
                newPageList = driver.find_element(By.CLASS_NAME, 'prev-next').find_elements(By.TAG_NAME, "a")
                # 강사모 게시판 페이지는 1000 에서 다음을 누르면 1 페이지로 되돌아감
                print("페이지 순환 체크")
                for newPage in newPageList:
                    newPageText = newPage.text.replace(',', '')
                    newPageIsSelected = newPage.get_attribute("class") == "on"
                    if newPageIsSelected:
                        if int(newPageText) <= int(pageText):
                            print("기존 페이지 : " + pageText + ", 새 페이지 : " + newPageText)
                            print("페이지 순환 -> 페이지 탐색 루프 탈출")
                            pageLoop = False
                        break
                break

print("완료 - 크롬 드라이버 종료")
driver.close()

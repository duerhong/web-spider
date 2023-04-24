from task import SpiderTask
task = SpiderTask()
ret = task.createTask(
    # Landing page, the first page crawling
    landing_page="https://www.test.com",
    # domain
    domain="www.test.com",
    # Website basic link, for the internal chain for stitching and crawling
    basic_page="https://www.test.com/"
)
if ret:
    print("successful")
else:
    print("Failure")

from retrying import retry


@retry(stop_max_attempt_number=5,stop_max_delay=30*1000)
def testRetry():
    try:
        # print(2)
        raise BaseException
    except BaseException as e:
        print('1')
        raise BaseException

if __name__ == '__main__':
    # testRetry()
    if None==None or len(None):
        pass
#####################################################################################################
#
#  Copyright (c) 2014 The CCP project authors. All Rights Reserved.
#
#  Use of this source code is governed by a Beijing Speedtong Information Technology Co.,Ltd license
#  that can be found in the LICENSE file in the root of the web site.
#
#   https://www.yuntongxun.com
#
#  An additional intellectual property rights grant can be found
#  in the file PATENTS.  All contributing project authors may
#  be found in the AUTHORS file in the root of the source tree.

from libs.ronglian_sms_sdk import algorithm
import requests
import time
import json
import traceback

class SmsSDK:
    """短信SDK"""

    # 容联云通讯服务地址
    url = 'https://app.cloopen.com:8883'
    # 发送短信URI
    sendMessageURI = '/2013-12-26/Accounts/{}/SMS/TemplateSMS'

    def __init__(self, accId, accToken, appId):
        self.__accId = accId
        self.__accToken = accToken
        self.__appId = appId

    def sendMessage(self, tid: str, mobile: str, datas: tuple) -> str:
        """发送短信
        Args:
            tid: 短信模板ID，容联云通讯网站自行创建
            mobile: 下发手机号码，多个号码以英文逗号分隔
            datas: 模板变量
        Returns:
            返回发送结果和发送成功消息ID
            发送成功示例:
            {"statusCode":"000000","templateSMS":{"dateCreated":"20130201155306",
             "smsMessageSid":"ff8080813c373cab013c94b0f0512345"}}
            发送失败示例：
            {"statusCode": "172001", "statusMsg": "网络错误"}
        """
        timestamp = time.strftime('%Y%m%d%H%M%S', time.localtime())
        url = self.__buildSendMessageUrl(timestamp)
        headers = self.__buildHeaders(timestamp)
        body = self.__buildSendMessageBody(tid, mobile, datas)
        self.__logRequestInfo(url, headers, body)
        try:
            r = requests.post(url, headers=headers, data=body, timeout=(2, 5))
            if (r.status_code == requests.codes.ok):
                print('Response body: ', r.text)
                return r.text
            else:
                return json.dumps({'statusCode': str(r.status_code)})
        except:
            traceback.print_exc()
            return '{"statusCode": "172001", "statusMsg": "网络错误"}'

    def __buildSendMessageUrl(self, timestamp):
        """构建发送短信URL"""
        return f'{self.url}{self.sendMessageURI.format(self.__accId)}?sig={self.__buildSign(timestamp)}'

    def __buildSign(self, timestamp):
        """构建签名sig
        Args:
            timestamp: 时间字符串 格式：yyyyMMddHHmmss
        Returns:
            签名大写字符串
        """
        plaintext = f'{self.__accId}{self.__accToken}{timestamp}'
        print("Sign plaintext: ", plaintext)
        return algorithm.md5(plaintext).upper()

    def __buildHeaders(self, timestamp):
        """构建请求报头"""
        headers = {}
        headers['Content-Type'] = 'application/json;charset=utf-8'
        headers['Accept'] = 'application/json'
        headers['Accept-Charset'] = 'UTF-8'
        headers['Authorization'] = self.__buildAuthorization(timestamp)
        return headers

    def __buildAuthorization(self, timestamp):
        """构建报头Authorization
        Args:
            timestamp: 时间字符串 格式：yyyyMMddHHmmss
        Returns:
            Authorization字符串
        """
        plaintext = f'{self.__accId}:{timestamp}'
        print("Authorization plaintext: %s" % plaintext)
        return algorithm.base64Encoder(plaintext)

    def __buildSendMessageBody(self, tid, mobile, datas):
        """构建发送短信报文"""
        body = {}
        body['to'] = mobile
        body['appId'] = self.__appId
        body['templateId'] = tid
        body['datas'] = datas
        return json.dumps(body)

    def __logRequestInfo(self, url, headers, body):
        """打印请求信息日志"""
        print('Request url: ', url)
        print('Request headers: ', headers)
        print('Request body: ', body)


if __name__ == '__main__':
    accId = '2c94811c8a27cf2d018a4c1f603a0e77'
    accToken = '0219af12249c4869871525c79b97ebe4'
    appId = '2c94811c8a27cf2d018a4c1f618f0e7e'

    def send_message():
        sdk = SmsSDK(accId, accToken, appId)
        tid = '1'
        mobile = '18283906566'
        datas = ('4561', '3')
        resp = sdk.sendMessage(tid, mobile, datas)
        print(resp)

    send_message()

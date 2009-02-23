import unittest
from myspace.myspaceapi import MySpace, MySpaceError

class ApiParameterValidationTest(unittest.TestCase):

  def setUp(self):
      self.ms = MySpace ('CONSUMER_KEY', 'CONSUMER_SECRET')
  
  def test_call_apis_with_negative_params(self):
      """Tests the calling of methods on the MySpace object by specifying negative param values. 
      """
      user_id = page = page_size = album_id = friend_ids = photo_id = video_id = -1

      self.assertRaises(MySpaceError, self.ms.get_albums, user_id)
      self.assertRaises(MySpaceError, self.ms.get_album, user_id, album_id)
      self.assertRaises(MySpaceError, self.ms.get_friends, user_id, page=page, page_size=page_size)
      self.assertRaises(MySpaceError, self.ms.get_friendship, user_id, friend_ids)
      self.assertRaises(MySpaceError, self.ms.get_mood, user_id)
      self.assertRaises(MySpaceError, self.ms.get_photos, user_id, page=page, page_size=page_size)
      self.assertRaises(MySpaceError, self.ms.get_photo, user_id, photo_id)
      self.assertRaises(MySpaceError, self.ms.get_profile, user_id)
      self.assertRaises(MySpaceError, self.ms.get_status, user_id)
      self.assertRaises(MySpaceError, self.ms.get_videos, user_id)
      self.assertRaises(MySpaceError, self.ms.get_video, user_id, video_id)

  def test_get_friends_listparam(self):
      """Tests the calling of get_friends with an invalid value for the "list" parameter
         valid values are: 'top', 'online', 'app'
      """
      user_id = 1234567
      self.assertRaises(MySpaceError, self.ms.get_friends, user_id, list="junk")

  def test_get_friends_showparam(self):
      """Tests the calling of get_friends with an invalid value for the "show" parameter
         valid values are: 'mood', 'status', 'online' separated by a "|" character
      """
      user_id = 1234567
      self.assertRaises(MySpaceError, self.ms.get_friends, user_id, show="junk,junk")

  def test_call_apis_without_token(self):
      """Tests the calling of methods on the MySpace object without specifying token key/secret.
         Note that the we're not specifying the oauth token key/secret in the constructor
         above which should result in a MySpaceError exception when trying to invoke APIs
      """
      user_id = album_id = friend_ids = photo_id = video_id = 1234567

      self.assertRaises(MySpaceError, self.ms.get_userid)
      self.assertRaises(MySpaceError, self.ms.get_albums, user_id)
      self.assertRaises(MySpaceError, self.ms.get_album, user_id, album_id)
      self.assertRaises(MySpaceError, self.ms.get_friends, user_id)
      self.assertRaises(MySpaceError, self.ms.get_friendship, user_id, friend_ids)
      self.assertRaises(MySpaceError, self.ms.get_mood, user_id)
      self.assertRaises(MySpaceError, self.ms.get_photos, user_id)
      self.assertRaises(MySpaceError, self.ms.get_photo, user_id, photo_id)
      self.assertRaises(MySpaceError, self.ms.get_profile, user_id)
      self.assertRaises(MySpaceError, self.ms.get_status, user_id)
      self.assertRaises(MySpaceError, self.ms.get_videos, user_id)
      self.assertRaises(MySpaceError, self.ms.get_video, user_id, video_id)

  
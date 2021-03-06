from __future__ import absolute_import

from datetime import datetime, timedelta

from kvkit import NotFoundError
from projecto.models import Comment
from projecto.apiv1.todos.models import Todo, ArchivedTodo

import unittest
from .utils import ProjectTestCase, new_todo, new_comment


class TestTodoAPI(ProjectTestCase):
  def base_url(self, postfix):
    return "/api/v1/projects/{}/todos{}".format(self.project.key, postfix)

  # We need to test for security problems like XSS here.

  def test_new_todo(self):
    self.login()
    response, data = self.postJSON(self.base_url("/"), data={"title": "A title"})

    self.assertStatus(200, response)
    self.assertTrue("key" in data)
    self.assertTrue("title" in data)
    self.assertEquals("A title", data["title"])
    self.assertTrue("author" in data)
    self.assertEquals(self.user.key, data["author"]["key"])

    response, data = self.postJSON(self.base_url("/"), data={"title": "A title", "content": "some content", "tags": ["a", "b", "c"]})
    self.assertStatus(200, response)
    self.assertTrue("key" in data)
    self.assertTrue("title" in data)
    self.assertEquals("A title", data["title"])
    self.assertTrue("author" in data)
    self.assertEquals(self.user.key, data["author"]["key"])
    self.assertTrue("content" in data)
    self.assertTrue("markdown" in data["content"])
    self.assertEquals("some content", data["content"]["markdown"])
    self.assertTrue("html" in data["content"])
    self.assertTrue("<p>some content</p>" in data["content"]["html"])
    self.assertTrue("tags" in data)
    self.assertEquals(["a", "b", "c"], data["tags"])

  def test_new_todo_reject_badrequest(self):
    self.login()
    response, data = self.postJSON(self.base_url("/"), data={"invalid": "invald"})
    self.assertStatus(400, response)

    self.postJSON(self.base_url("/"), data={"title": "title", "content": "content", "author": "invalid"})
    self.assertStatus(400, response)

  def test_new_todo_reject_permission(self):
    response, data = self.postJSON(self.base_url("/"), data={"title": "todo"})
    self.assertStatus(403, response)

    user2 = self.create_user("test2@test.com")
    self.login(user2)
    response, data = self.postJSON(self.base_url("/"), data={"title": "todo"})
    self.assertStatus(403, response)

  # TODO: this method
  # def test_new_todo_filter_xss(self):

  def test_update_todo(self):
    todo = new_todo(self.user, self.project, save=True)

    self.login()
    response, data = self.putJSON(self.base_url("/" + todo.key), data={"title": "todo2"})
    self.assertStatus(200, response)
    self.assertTrue("key" in data)
    self.assertEquals(todo.key, data["key"])
    self.assertEquals("todo2", data["title"])

    response, data = self.putJSON(self.base_url("/" + todo.key), data={"content": {"markdown": "aaaa"}})
    self.assertStatus(200, response)
    self.assertEquals("todo2", data["title"])
    self.assertTrue("content" in data)
    self.assertTrue("markdown" in data["content"])
    self.assertEquals("aaaa", data["content"]["markdown"])
    self.assertTrue("<p>aaaa</p>" in data["content"]["html"])

  def test_update_todo_reject_badrequest(self):
    todo = new_todo(self.user, self.project, save=True)

    self.login()
    response, data = self.putJSON(self.base_url("/" + todo.key), data={"author": "someauthor"})
    self.assertStatus(400, response)

    response, data = self.putJSON(self.base_url("/" + todo.key), data={"title": "title", "adfaf": "adfa"})
    self.assertStatus(400, response)

  def test_update_todo_reject_permission(self):
    todo = new_todo(self.user, self.project, save=True)

    response, data = self.putJSON(self.base_url("/" + todo.key), data={"title": "todo2"})
    self.assertStatus(403, response)

    user2 = self.create_user("test2@test.com")
    self.login(user2)
    response, data = self.putJSON(self.base_url("/" + todo.key), data={"title": "todo2"})
    self.assertStatus(403, response)

  def test_get_todo(self):
    todo = new_todo(self.user, self.project, title="todo", save=True)

    self.login()
    response, data = self.getJSON(self.base_url("/" + todo.key))
    self.assertStatus(200, response)

    self.assertEqual(todo.key, data["key"])
    self.assertEqual("todo", data["title"])
    self.assertEqual(self.user.key, data["author"]["key"])
    self.assertEqual(self.user.name, data["author"]["name"])

  def test_get_todo_reject_permission(self):
    todo = new_todo(self.user, self.project, save=True)

    response, data = self.getJSON(self.base_url("/" + todo.key))
    self.assertStatus(403, response)

    user2 = self.create_user("test2@test.com")
    self.login(user2)
    response, data = self.getJSON(self.base_url("/" + todo.key))
    self.assertStatus(403, response)

  def test_delete_todo(self):
    todo = new_todo(self.user, self.project, save=True)

    self.login()
    response, data = self.deleteJSON(self.base_url("/" + todo.key))
    self.assertStatus(200, response)

    with self.assertRaises(NotFoundError):
      Todo.get(todo.key)

    response, data = self.deleteJSON(self.base_url("/" + todo.key))
    self.assertStatus(404, response)

  def test_delete_todo_reject_permission(self):
    todo = new_todo(self.user, self.project, save=True)

    response, data = self.deleteJSON(self.base_url("/" + todo.key))
    self.assertStatus(403, response)

  def test_markdone_todo(self):
    todo = new_todo(self.user, self.project, save=True)

    self.login()
    response, data = self.postJSON(self.base_url("/" + todo.key + "/markdone"), data={"done": True})
    self.assertStatus(200, response)
    todo = Todo.get(todo.key)
    self.assertTrue(todo.done)

    response, data = self.postJSON(self.base_url("/" + todo.key + "/markdone"), data={"done": False})
    self.assertStatus(200, response)
    todo = Todo.get(todo.key)
    self.assertFalse(todo.done)

  def test_markdone_todo_reject_badrequest(self):
    todo = new_todo(self.user, self.project, save=True)

    self.login()
    response, data = self.postJSON(self.base_url("/" + todo.key + "/markdone"), data={"notdone": False})
    self.assertStatus(400, response)

    response, data = self.postJSON(self.base_url("/" + todo.key + "/markdone"), data={"done": False, "invalid": "invalid"})
    self.assertStatus(400, response)

  def test_markdone_todo_reject_permission(self):
    todo = new_todo(self.user, self.project, save=True)

    response, data = self.postJSON(self.base_url("/" + todo.key + "/markdone"), data={"done": True})
    self.assertStatus(403, response)

    user2 = self.create_user("test2@test.com")
    self.login(user2)
    response, data = self.postJSON(self.base_url("/" + todo.key + "/markdone"), data={"done": True})
    self.assertStatus(403, response)

  def test_index_todos(self):
    self.login()

    keys = set()
    for i in xrange(50):
      todo = new_todo(self.user, self.project, date=datetime.now() + timedelta(seconds=i*10), title=str(i), save=True)
      keys.add(todo.key)

    response, data = self.getJSON(self.base_url("/"))
    self.assertStatus(200, response)
    self.assertEquals(4, len(data))
    self.assertTrue("todos" in data)
    self.assertEquals(1, data["currentPage"])
    self.assertEquals(50, data["totalTodos"])
    self.assertEquals(20, data["todosPerPage"])

    self.assertEquals(20, len(data["todos"]))
    k = {t["key"] for t in data["todos"]}
    self.assertEquals(20, len(k))

    response, data = self.getJSON(self.base_url("/?page=2"))
    self.assertEquals(20, len(data["todos"]))
    self.assertEquals(2, data["currentPage"])
    self.assertEquals(50, data["totalTodos"])
    self.assertEquals(20, data["todosPerPage"])
    k.update({t["key"] for t in data["todos"]})
    self.assertEquals(40, len(k))

    response, data = self.getJSON(self.base_url("/?page=3"))
    self.assertEquals(10, len(data["todos"]))
    self.assertEquals(3, data["currentPage"])
    self.assertEquals(50, data["totalTodos"])
    self.assertEquals(20, data["todosPerPage"])
    k.update({t["key"] for t in data["todos"]})
    self.assertEquals(50, len(k))

    self.assertEquals(keys, k)

  def test_index_todos_reject_permission(self):
    response, data = self.getJSON(self.base_url("/"))
    self.assertStatus(403, response)

    user2 = self.create_user("test2@test.com")
    self.login(user2)

    response, data = self.getJSON(self.base_url("/"))
    self.assertStatus(403, response)

  def test_filter_todos(self):
    self.login()

    keys = []
    for i in xrange(30):
      todo = new_todo(self.user, self.project, date=datetime.now() + timedelta(seconds=i*10), title=str(i), tags=["tag1"], save=True)
      keys.append(todo.key)

    for i in xrange(30, 50):
      todo = new_todo(self.user, self.project, date=datetime.now() + timedelta(seconds=i*10), title=str(i), tags=["tag2"], save=True)
      keys.append(todo.key)

    for i in xrange(50, 57):
      new_todo(self.user, self.project, date=datetime.now() + timedelta(seconds=i*10), title=str(i), tags=["tag3"], save=True)

    response, data = self.getJSON(self.base_url("/filter?tags=tag1&tags=tag2&page=1"))
    self.assertStatus(200, response)
    self.assertEquals(4, len(data))
    self.assertTrue("todos" in data)
    self.assertEquals(1, data["currentPage"])
    self.assertEquals(50, data["totalTodos"])
    self.assertEquals(20, data["todosPerPage"])
    self.assertEquals(20, len(data["todos"]))
    k = [t["key"] for t in data["todos"]]

    response, data = self.getJSON(self.base_url("/filter?tags=tag1&tags=tag2&page=2"))
    self.assertEquals(2, data["currentPage"])
    self.assertEquals(50, data["totalTodos"])
    self.assertEquals(20, data["todosPerPage"])
    self.assertEquals(20, len(data["todos"]))
    k.extend([t["key"] for t in data["todos"]])

    response, data = self.getJSON(self.base_url("/filter?tags=tag1&tags=tag2&page=3"))
    self.assertEquals(3, data["currentPage"])
    self.assertEquals(50, data["totalTodos"])
    self.assertEquals(20, data["todosPerPage"])
    self.assertEquals(10, len(data["todos"]))
    k.extend([t["key"] for t in data["todos"]])

    self.assertEquals(set(keys), set(k))

  def test_filter_todos_reject_permission(self):
    response, data = self.getJSON(self.base_url("/filter"))
    self.assertStatus(403, response)

    user2 = self.create_user("test2@test.com")
    self.login(user2)

    response, data = self.getJSON(self.base_url("/filter"))
    self.assertStatus(403, response)

  def test_markdone(self):
    todo = new_todo(self.user, self.project, save=True)

    self.login()
    response, data = self.postJSON(self.base_url("/" + todo.key + "/markdone"), data={"done": True})
    self.assertStatus(200, response)

    self.assertTrue(Todo.get(todo.key).done)

    response, data = self.postJSON(self.base_url("/" + todo.key + "/markdone"), data={"done": False})
    self.assertStatus(200, response)

    self.assertFalse(Todo.get(todo.key).done)

  def test_markdone_reject_badrequest(self):
    todo = new_todo(self.user, self.project, save=True)

    self.login() # TODO: we really gotta refactor these
    response, data = self.postJSON(self.base_url("/" + todo.key + "/markdone"), data={"title": True})
    self.assertStatus(400, response)

    response, data = self.postJSON(self.base_url("/" + todo.key + "/markdone"), data={"title": True, "done": True})
    self.assertStatus(400, response)

  def test_markdone_reject_permission(self):
    todo = new_todo(self.user, self.project, save=True)

    response, data = self.postJSON(self.base_url("/" + todo.key + "/markdone"), data={"done": False})
    self.assertStatus(403, response)

  def test_list_tags(self):
    new_todo(self.user, self.project, tags=["tag1", "tag2", "another tag"], save=True)
    new_todo(self.user, self.project, tags=["tag1", "mrrow", "wut"], save=True)

    self.login()
    response, data = self.getJSON(self.base_url("/tags/"))
    self.assertStatus(200, response)
    self.assertEquals(1, len(data))
    self.assertTrue("tags" in data)
    data["tags"].sort()
    self.assertTrue(sorted(["tag1", "tag2", "mrrow", "wut", "another tag"]), data["tags"])

  def test_list_tags_reject_permission(self):
    new_todo(self.user, self.project, tags=["tag1", "tag2", "another tag"], save=True)

    response, data = self.getJSON(self.base_url("/tags/"))
    self.assertStatus(403, response)

  def test_archived_index(self):
    todo1 = new_todo(self.user, self.project, save=True)
    todo2 = new_todo(self.user, self.project, done=True, save=True)
    todo1.archive()
    todo2.archive()

    self.login()
    response, data = self.getJSON(self.base_url("/"), query_string={"archived": "1"})
    self.assertStatus(200, response)
    self.assertTrue("todos" in data)
    self.assertEquals(2, len(data["todos"]))
    k = [t["key"] for t in data["todos"]]
    self.assertTrue(todo1.key in k)
    self.assertTrue(todo2.key in k)

    response, data = self.getJSON(self.base_url("/"))
    self.assertStatus(200, response)
    self.assertEquals(0, len(data["todos"]))

  def test_archived_delete(self):
    todo1 = new_todo(self.user, self.project, save=True)
    self.login()

    response = self.delete(self.base_url("/" + todo1.key))
    self.assertStatus(200, response)

    with self.assertRaises(NotFoundError):
      Todo.get(todo1.key)

    todo1_again = ArchivedTodo.get(todo1.key)
    self.assertEquals(todo1.key, todo1_again.key)

  def test_really_delete(self):
    todo1 = new_todo(self.user, self.project, save=True)
    self.login()

    response = self.delete(self.base_url("/" + todo1.key), query_string={"really": "1"})
    self.assertStatus(200, response)

    with self.assertRaises(NotFoundError):
      ArchivedTodo.get(todo1.key)

    with self.assertRaises(NotFoundError):
      Todo.get(todo1.key)

  def test_delete_todo_with_comments(self):
    todo1 = new_todo(self.user, self.project, save=True)
    comment = new_comment(self.user, todo1.key, save=True)

    self.login()
    response = self.delete(self.base_url("/" + todo1.key), query_string={"really": "1"})
    self.assertStatus(200, response)

    with self.assertRaises(NotFoundError):
      Todo.get(todo1.key)

    with self.assertRaises(NotFoundError):
      ArchivedTodo.get(todo1.key)

    with self.assertRaises(NotFoundError):
      Comment.get(comment.key)

  def test_delete_archived(self):
    todo1 = new_todo(self.user, self.project, save=True)
    todo2 = new_todo(self.user, self.project, save=True)
    todo1 = todo1.archive()
    todo2 = todo2.archive()
    self.login()

    response = self.delete(self.base_url("/" + todo1.key), query_string={"really": "1", "archived": "1"})
    self.assertStatus(200, response)

    with self.assertRaises(NotFoundError):
      todo1.reload()

    # Should not have an effect.
    response = self.delete(self.base_url("/" + todo2.key), query_string={"archived": "1"})
    self.assertStatus(304, response)
    todo2.reload()

  def test_get_archived(self):
    todo1 = new_todo(self.user, self.project, save=True)
    todo1 = todo1.archive()
    self.login()

    response, data = self.getJSON(self.base_url("/" + todo1.key))
    self.assertStatus(404, response)

    response, data = self.getJSON(self.base_url("/" + todo1.key), query_string={"archived": "1"})
    self.assertStatus(200, response)
    self.assertEquals(todo1.key, data["key"])

  def test_markdone_archived(self):
    todo1 = new_todo(self.user, self.project, save=True)
    todo1 = todo1.archive()
    self.login()

    response, data = self.postJSON(self.base_url("/" + todo1.key + "/markdone"), data={"done": True})
    self.assertStatus(404, response)

    response, data = self.postJSON(self.base_url("/" + todo1.key + "/markdone"), query_string={"archived": "1"}, data={"done": True})
    self.assertStatus(200, response)

    response, data = self.getJSON(self.base_url("/" + todo1.key), query_string={"archived": "1"})
    self.assertStatus(200, response)
    self.assertEquals(True, data["done"])


if __name__ == "__main__":
  unittest.main()

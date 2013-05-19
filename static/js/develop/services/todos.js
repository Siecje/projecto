"use strict";

(function(){
  angular.module("projecto").service(
    "TodosService", [function(){

      var apiUrl = function(project_id, postfix) {
        return window.API_PREFIX + "/projects/" + project_id + "/todos/" + (postfix ? postfix : "");
      };

      this.new = function(project, todo) {
        return $.ajax({
          type: "POST",
          url: apiUrl(project.key),
          dataType: "json",
          contentType: "application/json",
          data: JSON.stringify(todo)
        });
      };

      this.index = function(project) {
        return $.ajax({
          type: "GET",
          url: apiUrl(project.key),
          dataType: "json"
        });
      };

      this.delete = function(project, todo) {
        return $.ajax({
          type: "DELETE",
          url: apiUrl(project.key, todo.key),
          dataType: "json"
        });
      };

      this.get = function(project, todoId) {
        return $.ajax({
          type: "GET",
          url: apiUrl(project.key, todoId),
          dataType: "json"
        });
      };

      this.put = function(project, todo) {
        return $.ajax({
          type: "PUT",
          url: apiUrl(project.key, todo.key),
          dataType: "json",
          contentType: "application/json",
          data: JSON.stringify(todo)
        });
      };
    }]
  );
})();
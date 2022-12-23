# Yr Search Layers Plugin  
https://github.com/NationalSecurityAgency/qgis-searchlayers-plugin  
This repository is intended as a contribution to qgis-searchlayers-plugin, to provide a test environment before PULL requests and to add functionality that is too proprietary.  
（日本語）  
このリポジトリは qgis-searchlayers-plugin への貢献として、PULL リクエスト前のテスト環境の提供や、独自すぎる機能の追加を目的としています。  
## Latest Japanese environment
## Realization of custom settings for each project
 By specifying the layer name in the 'searchlayers-plugin' variable in the project file, only the specified layer can be specified as the search layer.   
（日本語）  
プロジェクトファイルの変数 'searchlayers-plugin' にレイヤー名を指定することで、指定したレイヤーのみを検索レイヤに指定できます。  
#### ・normal
 ![image](https://user-images.githubusercontent.com/86514652/181909319-7436b72d-5c2f-49b0-b5be-2c8482644a4e.png)  
#### ・Set the variable 'searchlayers-plugin' in the project file to the name of the layer you want to specify.  
　　(Example) 'test1,test3,test10'.    
  　　 Separate layer names with ,.   
（日本語） プロジェクトファイルの変数 'searchlayers-plugin' に　指定したいレイヤ名を設定。   
　　（例）’test1,test3,test10'.  
  　 レイヤー名は , で区切ってください。  
    
 ![image](https://user-images.githubusercontent.com/86514652/181909555-981fb82a-ce43-4255-b674-de02511fd0c0.png)  
#### ・result:  
 ![image](https://user-images.githubusercontent.com/86514652/181909585-7cc2ad58-779e-409a-9fcb-7f1dd8f5dfce.png)  

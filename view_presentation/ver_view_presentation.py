import pandas as pd
import math, random
from ipywidgets import *

from view_presentation.interface import embedding_distance
#from view_presentation.interface.attribute_content_interface import AttributeContentInterface
import view_presentation.config as config
import view_presentation.interface_list as interface_lst
import view_presentation.interface as int_folder
import ipywidgets as widgets

from IPython.display import clear_output, Markdown

random.seed(config.seed)

#Right now, same question can be asked by multiple interfaces. Ignored candidates of different interfaces do not share information.
#Sharing that info can improve complexity

class ViewPresentation:
    def __init__(self,query, df_lst):
        self.interface_options=[]
        self.asked={}
        self.total_questions=0
        self.answered={}

        self.query = query
        self.embedding_obj = embedding_distance.EmbeddingModel()
        self.initialize_candidates(df_lst)

        #dataframe index is the key and value denotes the number of times it is ignored/shortlisted
        self.ignored_datasets={}
        self.shortlisted_datasets={}
        
        for interface in self.interface_options:
            self.answered[interface]=0
            self.asked[interface]=0
        

    #Add a function to initialize the candidates for each interface
    def initialize_candidates(self,df_lst):
        iter=0
        self.df_lst=df_lst
        for curr_interface in interface_lst.interface_options:
            aci = curr_interface(str(iter),self.embedding_obj)
            aci.generate_candidates(self.df_lst)
            aci.rank_candidates(self.query)
            self.interface_options.append(aci)
            iter+=1
    
        

    # ranking of questions
    def update_output(self,b):
        #print ("updated output")
        res= (self.result)
        coverage_lst=res[-1]
        self.choose_interface()
        #print (res)
        #print (res[0])
        try:
            out_index= res[0].index(res[1].value)
        except:
            out_index=0
        if out_index==0:
            for df_iter in coverage_lst:
                if df_iter in self.shortlisted_datasets.keys():
                    self.shortlisted_datasets[df_iter]+=1
                else:
                    self.shortlisted_datasets[df_iter]=1
        elif out_index==1:
            for df_iter in coverage_lst:
                if df_iter in self.ignored_datasets.keys():
                    self.ignored_datasets[df_iter]+=1
                else:
                    self.ignored_datasets[df_iter]=1


        # print ("this",out_index,self.shortlisted_datasets,self.ignored_datasets)

        return
    

    def get_shortlisted_datasets(self,b=None):
        print ("shortlisted datasets are")
        '''for iter in shortlisted:
            print ("---------------------")
            display(self.df_lst[iter])
            print ("---------------------")
        '''
        clear_output(wait=True)
        self.goback = widgets.Button(
                description='Answer More',
                disabled=False,
                button_style='', # 'success', 'info', 'warning', 'danger' or ''
                tooltip='Submit',
                icon='' # (FontAwesome names without the `fa-` prefix)
            )
        self.goback.on_click(self.choose_interface)
        display(self.goback)

        final_scores={}
        for df_iter in self.shortlisted_datasets.keys():
            final_scores[df_iter] = self.shortlisted_datasets[df_iter]
            if df_iter in self.ignored_datasets.keys():
                final_scores[df_iter]-=self.ignored_datasets[df_iter]
        scores = sorted(final_scores.items(), key=lambda item: item[1],reverse=True)
        
        iter=1
        for (score,df_iter) in scores:
            print ("Rank ",iter)
            self.download = widgets.Button(
                description='Download',
                disabled=False,
                button_style='', # 'success', 'info', 'warning', 'danger' or ''
                tooltip='Submit',
                icon='' # (FontAwesome names without the `fa-` prefix)
            )
            #self.download.on_click(self.choose_interface)
            display(self.df_lst[df_iter].head(10),self.download)
            iter+=1

        # print (scores)


    def choose_interface(self,b=None):

        threshold=math.ceil(math.log(len(self.interface_options))*1.0/math.log(2))
        
        clear_output(wait=True)

        display(Markdown('<h1><center><strong>{}</strong></center></h1>'.format("View Presentation")))

        gamma=config.gamma

        scores=[]
        corresponding_ques=[]
        iter=0
        choose_random=False
        valid_interfaces=[]
        coverage_lst=[]

        for interface in self.interface_options:#move to config.py
            try:
                score,ques,coverage=interface.get_question(list(self.ignored_datasets.keys()))
            except:
                continue
            #print (interface.name,score,ques,coverage)
            answer_prob=1
            if ques is not None and  self.asked[interface]<threshold:
                choose_random=True
            elif ques is not None:
                answer_prob=self.answered[interface]*1.0/self.asked[interface]
            #this is w(I)
            if ques is not None:
                answer_prob=0
                valid_interfaces.append(interface)
                scores.append(answer_prob*score)
                corresponding_ques.append(ques)
                coverage_lst.append(coverage)
            iter+=1
        if len(valid_interfaces)==0:
            return None,None,None
        if choose_random:
            max_index=self.total_questions % len(self.interface_options)#random.randint(0,len(scores)-1)#scores.index(max(scores))
            #print (max_index,"choosing randomly")
        else:
            #Toss a coin with prob. TODO
            total_score=sum(scores)
            i=0
            randval=random.random()

            for interface in valid_interfaces:
                #print (i)
                if total_score>0:
                    scores[i]=(1-gamma)*scores[i]*1.0/total_score + gamma*1.0/len(valid_interfaces)
                else:
                    scores[i]=1.0/len(valid_interfaces)
                if randval<scores[i]:
                    break
                randval-=scores[i]
                i+=1
            max_index=i
        #print ("Current question",max_index)
        self.total_questions+=1
        #print ("chosen interface",self.interface_options[max_index])
        #print (max_index,valid_interfaces,corresponding_ques)
        self.result = valid_interfaces[max_index].ask_question(corresponding_ques[max_index],self.df_lst)
        self.result.append(coverage_lst[max_index])
        self.result[2].on_click(self.update_output)
        self.shortlisted_datasets_button = widgets.Button(
                description='Show\n Shortlist',
                disabled=False,
                button_style='', # 'success', 'info', 'warning', 'danger' or ''
                tooltip='Submit',
                icon='' # (FontAwesome names without the `fa-` prefix)
            )
        self.shortlisted_datasets_button.on_click(self.get_shortlisted_datasets)
        display(HBox([self.shortlisted_datasets_button], layout= Layout(width='100%')))
        '''
        if result==1:
            for df_iter in coverage_lst[max_index]:
                if df_iter in self.shortlisted_datasets.keys():
                    self.shortlisted_datasets[df_iter]+=1
                else:
                    self.shortlisted_datasets[df_iter]=1
        elif result==2:
            for df_iter in coverage_lst[max_index]:
                if df_iter in self.ignored_datasets.keys():
                    self.ignored_datasets[df_iter]+=1
                else:
                    self.ignored_datasets[df_iter]=1


        print ("this",self.shortlisted_datasets,self.ignored_datasets)
        '''
        #Use responses to update shortlisted and ignored ones



      
        return valid_interfaces[max_index], corresponding_ques[max_index], coverage_lst[max_index]
    


#example usage of the interface
if __name__ == '__main__':

    data1 = ["Chicago","NYC","SF","Seattle"]
    df1 = pd.DataFrame(data1, columns=['City'])
  
    data2 = ["Paris","Copenhagen","Delhi","Sydney"]
    df2 = pd.DataFrame(data2, columns=['international city'])


    data3 = ["Paris","Copenhagen","Delhi","Sydney"]
    df3 = pd.DataFrame(data2, columns=['international city'])

    df_lst=[df1, df2, df3]

    query = "new york city datasets"
    vp = ViewPresentation(query, df_lst)
    iter=0
    while iter<5:
        vp.choose_interface()
        iter+=1

